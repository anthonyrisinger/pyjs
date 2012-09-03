// Copyright (C) 2012 C Anthony Risinger <anthony@xtfx.me>
//
// LICENSE: Apache 2.0 <http://www.apache.org/licenses/LICENSE-2.0.txt>
//
// window, document, and others passed in arguments


var Marshaller = {

    OK: 200,

    MOVED: 301,
    FOUND: 302,

    BAD_REQUEST: 400,
    NOT_FOUND: 404,
    NOT_ALLOWED: 405,
    NOT_ACCEPTABLE: 406,
    INTERNAL_ERROR: 500,
    NOT_IMPLEMENTED: 501,

    _id: None,
    _bus: None,
    _key: None,
    _ref: None,
    _sig: None,
    _req: None,
    _res: {
        head: None,
        data: None,
        },

    __init__: function(id, bus, key){
        this._id = id;
        this._bus = bus;
        this._key = key;
        this._ref = window[key];
        this._sig = document.createEvent('Event');
        this._sig.initEvent(id.remote, 0, 0);
        this._req = {};
        this._res = {};
        this._req.head = this._res.head = None;
        this._req.data = this._res.data = None;
        },

    send: function(code){
        var req = this._req;
        var res = this._res;
        code = parseInt(code);
        (code > 199) || (code = this.INTERNAL_ERROR);
        (code < 600) || (code = this.INTERNAL_ERROR);

        if(res.head.parentNode !== undefined){

            };
        this.pkt.data = dumps(res);
        this.link.dispatchEvent(ok_evt);
        this.header.data = '';
        },

    get_proto_map: function(pkt){
        logger.log('proto! ' + pkt);
        },

    };
Marshaller.__init__.prototype = Marshaller;
Marshaller = Marshaller.__init__;

var ok_evt = document.createEvent('Event');
ok_evt.initEvent(uugi, 0, 0);

window.addEventListener(uujs, function(e){

    var p = window.XMLHttpRequest;
    var o = new p();
    p = p.prototype;
    var buf = e.relatedTarget;
    var io = buf.firstChild;

    buf.addEventListener(uujs, function(e){
        var pkt = loads(io.data);

        switch(pkt.type){
        case undefined:
            //TODO: EXCEPTION
        case 'get_proto_map':
            logger.log('proto! ' + pkt);
            break;
        case 'query':
            //logger.log('query! ' + pkt.key);
            if(p[pkt.key] !== undefined){
                io.data = dumps({
                    code: 200,
                    type: (typeof p[pkt.key]),
                    key: pkt.key,
                    proto: true,
                    });
                buf.dispatchEvent(ok_evt);
                io.data = None;
            } else if(o[pkt.key] !== undefined){

            } else {

            };
            break;
        case 'call':
            var frame = [];
            var nargs = pkt.nargs;
            var ptr = buf.lastChild.firstChild;
            while (ptr && frame.length<nargs){
                frame.push(ptr.data);
                ptr = ptr.nextSibling;
            };
            //TODO: undef
            //logger.log(o[pkt.key].apply(o, frame));
            break;
        default:
            logger.log('unknown packet...');
            break;
        };

        });
    });
