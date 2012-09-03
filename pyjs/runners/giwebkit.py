# Copyright (C) 2012 C Anthony Risinger <anthony@xtfx.me>
#
# LICENSE: Apache 2.0 <http://www.apache.org/licenses/LICENSE-2.0.txt>

import os
import sys
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger(__name__).setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

import re
import json
from urllib import urlopen
from urlparse import urljoin

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Soup
from gi.repository import WebKit

import types
import signal
import operator
from functools import partial
from traceback import print_exc
from pprint import pformat
from uuid import uuid4


sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)


#TODO: impl collections.MutableMapping
class URI(object):

    KEYS = [f.get_name() for f in Soup.URI.__info__.get_fields()]

    get_keys = staticmethod(operator.attrgetter(*KEYS))

    @staticmethod
    def items(uri):
        return zip(URI.KEYS, URI.get_keys(uri))


class Marshaller(object):

    _UUID = uuid4().hex

    _ctx = None
    _buf = None

    def __init__(self, wnd, target='XMLHttpRequest'):
        doc = wnd.document
        ctx = self._ctx = doc._ctx
        buf = self._buf = wnd.document.createDocumentFragment()
        stack = self.stack = doc.createElement('stack')
        proto = self.proto = doc.createElement('proto')

        buf.appendChild(doc.createTextNode(''))
        buf.appendChild(stack)
        buf.appendChild(proto)

        sig = doc.createEvent('MouseEvent')
        sig.initMouseEvent(
            self._UUID, 0, 0, wnd, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, buf
            )

        wnd.dispatchEvent(sig)
        ctx.addEventListener(buf, self._UUID[::-1], self)

        sig = self._sig = doc.createEvent('Event')
        sig.initEvent(self._UUID, 0, 0)

    def __getattr__(self, key):
        ctx = self._ctx
        buf = self._buf
        qnode = buf.firstChild
        qnode.data = json.dumps({'type': 'query', 'key': key})
        buf.dispatchEvent(self._sig)
        qnode.data = ''
        return getattr(self, key)

    def __setattr__(self, key, attr):
        print self, key, attr
        super(Marshaller, self).__setattr__(key, attr)

    def __call__(self, frag, evt, cap):
        pkt = json.loads(frag.firstChild.data)
        key = str(pkt['key'])
        cls = self.__class__
        tgt = self
        inst = self
        if pkt['proto']:
            tgt = cls
            inst = None
        if pkt['type'] == 'function':
            f = partial(self.__call, _key=key)
            f.__name__ = key
            setattr(tgt, key, f)

    def __call(self, *args, **kwds):
        key = kwds.get('_key')
        buf = self._buf
        ctx = self._ctx
        doc = ctx.getDomDocument()
        stack = buf.firstChild
        frame = buf.lastChild
        ptr = frame.firstChild
        for arg in args:
            if ptr is None:
                ptr = doc.createTextNode('')
                frame.appendChild(ptr)
            ptr.data = arg
            ptr = ptr.nextSibling
        while ptr is not None:
            ptr.data = ''
            ptr = ptr.nextSibling
        stack.data = json.dumps({'type': 'call',
                                 'key': key,
                                 'nargs': len(args)})
        buf.dispatchEvent(self._sig)
        ret = stack.data
        stack.data = ''
        return ret

    @classmethod
    def _bind(cls, key):
        owner, attr = key
        return types.MethodType(cls, None, owner)

    @classmethod
    def _link(cls, ctx):
        from _utils import jscript
        args = {
            'uujs': repr(cls._UUID),
            'uugi': repr(cls._UUID[::-1]),
            }
        ctx._view.execute_script(jscript('marshaller.js', args))


class GITimer(object):

    _UUID = uuid4().hex

    key = None

    def __init__(self, key):
        self.key = key

    def __call__(self, wnd, cb, ms):
        doc = wnd.document
        ctx = doc._ctx

        buf = doc.createTextNode(self.key)
        sig = doc.createEvent('MouseEvent')
        sig.initMouseEvent(
            self._UUID, 0, 0, wnd, ms, 0,
            0, 0, 0, 0, 0, 0, 0, 0, buf
            )

        wnd.dispatch_event(sig)
        ctx.addEventListener(buf, self._UUID[::-1], cb)
        return int(buf.data)

    @classmethod
    def _bind(cls, key):
        owner, attr = key
        return types.MethodType(cls(attr), None, owner)

    @classmethod
    def _link(cls, ctx):
        # GITimer: ready the listener
        ctx._view.execute_script(r'''
            (function(wnd, doc, uujs, uugi, undefined){
                wnd.addEventListener(uujs, function(e){
                    var buf = e.relatedTarget;
                    var evt = doc.createEvent('Event');
                    evt.initEvent(uugi, 0, 0);
                    buf.data = wnd[buf.data](function(){
                        buf.dispatchEvent(evt);
                    }, e.detail);
                });
            })(window, document, %r, %r);
            ''' % (cls._UUID, cls._UUID[::-1]))


class GIProxy(object):

    key = None
    getter = None
    setter = None

    def __init__(self, key, impl='property'):
        self.key = key
        self.getter = operator.methodcaller('get_%s' % impl, key)
        self.setter = operator.attrgetter('set_%s' % impl)

    def __get__(self, inst, type_gi):
        return self.getter(inst)

    def __set__(self, inst, attr):
        self.setter(inst)(self.key, attr)

    def __delete__(self, inst):
        pass


class GILocation(object):

    _ctx = None

    def __init__(self, ctx):
        #TODO: use SoupURI for this instead
        Soup.URI.new()
        def update(doc, pspec=None):
            a.set_href(doc.get_document_uri())
            logger.debug('location:%s', a.get_href())
        doc = app._doc
        a = doc.createElement('a')
        doc.connect('notify::document-uri', update)
        update(doc)
        object.__setattr__(self, '_app', app)
        object.__setattr__(self, '_a', a)

    def __getattr__(self, key):
        return getattr(self._a, key)

    def __setattr__(self, key, attr):
        #TODO: needs to interact with view.load_uri()
        setattr(self._a, key, attr)

    def assign(self):
        #TODO
        self._app._wnd.get_history()

    def reload(self):
        self._app._view.reload()

    def replace(self):
        #TODO
        self._app._wnd.get_history()

    @classmethod
    def _bind(cls, key):
        owner, attr = key
        return types.MethodType(cls(key), None, owner)


class Resolver(object):

    NONE = object()
    UPPER = re.compile('([A-Z])')

    _custom = {
        (WebKit.DOMDOMWindow, 'XMLHttpRequest'): Marshaller,
        (WebKit.DOMDOMWindow, 'setInterval'): GITimer,
        (WebKit.DOMDOMWindow, 'setTimeout'): GITimer,
        (WebKit.DOMDOMWindow, 'location'): GILocation,
        #TODO: this is actually a bug in pyjs ... UIEvents
        #      do not have these attributes.
        (WebKit.DOMUIEvent, 'shiftKey'): False,
        (WebKit.DOMUIEvent, 'ctrlKey'): False,
        (WebKit.DOMUIEvent, 'altKey'): False,
        }

    _type_gi = None

    def __init__(self, type_gi):
        method = types.MethodType(self, None, type_gi)
        type.__setattr__(type_gi, '__getattr__', method)
        type.__setattr__(type_gi, '__setattr__', method)
        self._type_gi = type_gi

    def __call__(self, inst, key, attr=NONE):
        if attr is self.NONE:
            return self.getattr(inst, key)
        self.setattr(inst, key, attr)

    def getattr(self, inst, key):
        for impl in (self.getattr_gi, self.getattr_w3):
            attr = impl(inst, key)
            if attr is not self.NONE:
                logger.debug('%s:%s.%s', impl.__name__,
                    inst.__class__.__name__, key)
                return attr
        raise AttributeError('%r object has no attribute %r' % (
                                    inst.__class__.__name__, key))

    def getattr_gi(self, inst, key):
        try:
            if inst.get_data(key) is None:
                return self.NONE
        except TypeError:
            return self.NONE
        type.__setattr__(inst.__class__, key, GIProxy(key, 'data'))
        return getattr(inst, key)

    def getattr_w3(self, inst, key_w3):
        key_gi = self._key_gi(key_w3)
        for base in inst.__class__.__mro__:
            key = (base, key_w3)
            if key in self._custom:
                try:
                    attr = self._custom[key]._bind(key)
                except AttributeError:
                    attr = self._custom[key]
            elif hasattr(inst.props, key_gi):
                attr = GIProxy(key_gi)
            elif key_gi in base.__dict__:
                attr = base.__dict__[key_gi]
            else:
                continue
            type.__setattr__(base, key_w3, attr)
            return getattr(inst, key_w3)
        return self.NONE

    def setattr(self, inst, key, attr):
        # hasattr() *specifically* chosen because it calls getattr()
        # internally, possibly setting a proxy object; if True, super()
        # will then properly setattr() against the proxy or instance.
        if hasattr(inst, key):
            super(self._type_gi, inst).__setattr__(key, attr)
        else:
            inst.set_data(key, attr)
            logger.debug('setattr(inst, %r, attr):\n%s', key,
                pformat([('inst', inst), ('attr', attr)]))

    def _key_gi(self, key):
        return self.UPPER.sub(r'_\1', key).lower()


class Callback(object):

    def __init__(self, sender, cb, boolparam):
        self.sender = sender
        self.cb = cb
        self.boolparam = boolparam

    def _callback(self, sender, event, data):
        try:
            return self.cb(self.sender, event, self.boolparam)
        except:
            print_exc()
            return None


class ApplicationFrame(object):

    #TODO: split RunnerContext (multi-frame support)
    pass


class RunnerContext(object):

    platform = 'webkit'
    uri = 'about:blank'
    #TODO: rename, accidentally removed?
    appdir = None
    width = 800
    height = 600
    # TODO: change WebKit patch to hold reference
    listeners = None

    def __init__(self):
        self.listeners = dict()

    def run(self):
        logger.debug('mainloop:entering...')
        Gtk.main()
        logger.debug('mainloop:exiting...')

    def setup(self, uri=uri, **kwds):
        for k, v in kwds.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)
        if '://' not in uri:
            uri = 'file://%s' % os.path.abspath(uri)

        uri = self.uri = Soup.URI.new(uri)
        logger.info('uri:\n%s', pformat(URI.items(uri)))

        view = self._view = WebKit.WebView()
        toplevel = self._toplevel = Gtk.Window()
        scroller = self._scroller = Gtk.ScrolledWindow()
        toplevel.set_default_size(self.width, self.height)
        toplevel.add(scroller)
        scroller.add(view)

        quit_accel = Gtk.AccelGroup.new()
        quit_key, quit_mask = Gtk.accelerator_parse('<Ctrl>q')
        quit_key2, quit_mask2 = Gtk.accelerator_parse('<Ctrl>w')
        quit_accel.connect(quit_key, quit_mask, 0, self._quit_cb)
        quit_accel.connect(quit_key2, quit_mask2, 0, self._quit_cb)

        back_accel = Gtk.AccelGroup.new()
        back_key, back_mask = Gtk.accelerator_parse('<Alt>Left')
        back_accel.connect(back_key, back_mask, 0, self._history_last_cb)

        fwd_accel = Gtk.AccelGroup.new()
        fwd_key, fwd_mask = Gtk.accelerator_parse('<Alt>Right')
        fwd_accel.connect(fwd_key, fwd_mask, 0, self._history_next_cb)

        view.load_uri(self.uri.to_string(0))

        view.connect('onload-event', self._frame_loaded_cb)
        view.connect('title-changed', self._title_changed_cb)
        view.connect('icon-loaded', self._icon_loaded_cb)
        view.connect('populate-popup', self._populate_popup_cb)
        view.connect('console-message', self._console_message_cb)
        #view.connect('resource-content-length-received',
        #             self._resource_recv_cb, None)
        #view.connect('resource-request-starting',
        #             self._resource_init_cb, None)

        settings = view.get_property('settings')
        settings.set_property('auto-resize-window', True)
        settings.set_property('enable-file-access-from-file-uris', True)
        settings.set_property('enable-accelerated-compositing', True)
        settings.set_property('enable-webgl', True)

        # GLib.PRIORITY_LOW == 300
        GObject.timeout_add(1000, self._idle_loop_cb, priority=300)
        signal.signal(signal.SIGINT, self._quit_cb)
        toplevel.connect('destroy', self._quit_cb)
        toplevel.add_accel_group(quit_accel)
        toplevel.add_accel_group(back_accel)
        toplevel.add_accel_group(fwd_accel)

        # display and run mainloop (returns after frame load)
        toplevel.show_all()
        #TODO: breaks reload/navigation :-( need to detect or impl differently
        Gtk.main()

    def getUri(self):
        return self.uri.to_string(0)

    def _idle_loop_cb(self):
        # mostly here to enable Ctrl^C/SIGINT without resorting to:
        #     signal.signal(signal.SIGINT, signal.SIG_DFL)
        # ... but could be useful in future; active timeout required else
        # SIGINT is not be processed until the next Gdk event
        return True

    def _console_message_cb(self, view, message, lineno, source):
        logger.debug('JAVASCRIPT:%s:%s', lineno, message)
        return True

    def _resource_init_cb(self, view, frame, webres, req, res, data):
        m = req.get_message()
        content_type = m.request_headers.get_content_type()[0]
        if content_type is not None:
            if content_type.startswith('application/json'):
                print 'JSONRPC!'

    def _resource_recv_cb(self, view, frame, res, length, data):
        #m = res.get_network_request().get_message()
        #print m.request_headers.get_content_type()
        print res.props.mime_type, res.props.uri

    def _frame_loaded_cb(self, view, frame):
        #TODO: research multiple apps
        if frame is not view.get_main_frame():
            logger.debug('sub-frame: %s', frame)
            return

        self._doc = self._view.get_dom_document()
        self._wnd = self._doc.get_default_view()
        self._doc._ctx = self

        Marshaller._link(self)
        GITimer._link(self)

        #TODO: redundant? incompat with poly-frame/reload!
        import __pyjamas__
        __pyjamas__.set_gtk_module(Gtk)
        __pyjamas__.set_main_frame(self)

        #TODO: made this work ... and skip bootstrap.js
        #for m in __pyjamas__.pygwt_processMetas():
        #    minst = module_load(m)
        #    minst.onModuleLoad()

        # return control to setup()
        Gtk.main_quit()

    def _icon_loaded_cb(self, view, icon_uri):
        current = view.get_property('uri')
        dom = view.get_dom_document()
        icon = (Gtk.STOCK_DIALOG_QUESTION, None, 0)
        found = set()
        found.add(icon_uri)
        found.add(urljoin(current, '/favicon.ico'))
        scanner = {
            'href': dom.querySelectorAll(
                        'head link[rel~=icon][href],'
                        'head link[rel|=apple-touch-icon][href]'
                        ),
            'content': dom.querySelectorAll(
                        'head meta[itemprop=image][content]'
                        ),
            }
        for attr in scanner.keys():
            for i in xrange(scanner[attr].length):
                uri = getattr(scanner[attr].item(i), attr)
                if len(uri) == 0:
                    continue
                found.add(urljoin(current, uri))
        for uri in found:
            fp = urlopen(uri)
            if fp.code != 200:
                continue
            i = fp.info()
            if i.maintype == 'image' and 'content-length' in i:
                try:
                    ldr = Gtk.gdk.PixbufLoader()
                    ldr.write(fp.read(int(i['content-length'])))
                    ldr.close()
                except:
                    continue
                pb = ldr.get_pixbuf()
                pbpx = pb.get_height() * pb.get_width()
                if pbpx > icon[2]:
                    icon = (uri, pb, pbpx)
        if icon[1] is None:
            self._toplevel.set_icon_name(icon[0])
        else:
            self._toplevel.set_icon(icon[1])
        logger.debug('icon:%s', icon[0])

    def mash_attrib(self, name, joiner='-'):
        return name

    def alert(self, msg):
        self._wnd.alert(msg)

    def _populate_popup_cb(self, view, menu):
        menu.append(Gtk.SeparatorMenuItem.new())
        go = lambda signal, uri: view.load_uri(uri)
        entries = [
            ('About WebKit', 'http://live.gnome.org/WebKitGtk'),
            ('About pyjs.org', 'http://pyjs.org/About.html'),
            ]
        for label, uri in entries:
            entry = Gtk.MenuItem(label=label)
            entry.connect('activate', go, uri)
            menu.append(entry)
        menu.show_all()

    def getDomWindow(self):
        return self._wnd

    def getDomDocument(self):
        return self._doc

    def getXmlHttpRequest(self):
        return self._wnd.XMLHttpRequest()

    def addWindowEventListener(self, event_name, cb):
        cb = Callback(self, cb, True)
        listener = WebKit.dom_create_event_listener(cb._callback, None)
        self._wnd.add_event_listener(event_name, listener, False)
        self.listeners[listener] = self._wnd

    def addXMLHttpRequestEventListener(self, element, event_name, cb):
        cb = Callback(element, cb, True)
        setattr(element, "on%s" % event_name, cb._callback)

    def addEventListener(self, element, event_name, cb):
        cb = Callback(element, cb, False)
        listener = WebKit.dom_create_event_listener(cb._callback, None)
        element.add_event_listener(event_name, listener, False)
        self.listeners[listener] = element

    def _quit_cb(self, *args):
        logger.debug('destroy:draining events...')
        Gtk.main_quit()

    def _title_changed_cb(self, view, frame, title):
        self._toplevel.set_title(title)

    def _history_last_cb(self, accel, window, key, mask):
        if self._view.can_go_back():
            self._view.go_back()

    def _history_next_cb(self, accel, window, key, mask):
        if self._view.can_go_forward():
            self._view.go_forward()

    window = property(getDomWindow)
    document = property(getDomDocument)

    _alert = alert
    _addEventListener = addEventListener
    _addWindowEventListener = addWindowEventListener
    _addXMLHttpRequestEventListener = addXMLHttpRequestEventListener


resolver = Resolver(WebKit.DOMObject)
context = RunnerContext()
setup = context.setup
run = context.run
