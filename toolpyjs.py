#!/usr/bin/env python2
# encoding: utf-8

import sys
import os

pyjspth = r'/home/anthony/projects/upstream/pyjs'
sys.path[0:0] = [r'/home/anthony/projects/upstream/pyjs/pyjs/src']
import pyjs
sys.path.append(os.path.join(pyjspth, 'pgen'))

from pyjs import translator

from pprint import pprint as pp
from pdb import set_trace as dd
from waflib.Build import BuildContext


def options(ctx):
	gr = ctx.add_option_group('translator options')
	translator.add_compile_options(gr)


def configure(ctx):
	print('config ...')


def debug(ctx):
	"""this is how we doo it"""
	ctx(rule='touch ${TGT}', target='foo.txt')
	ctx(rule='cp ${SRC} ${TGT}', source='foo.txt', target='bar.txt')
	ctx(rule='../../bin/pyjscompile -o ${TGT} ${SRC}', source='test.py', target='test.js')


def build(ctx):
	ctx(rule='touch ${TGT}', target='foo.txt')
	ctx(rule='cp ${SRC} ${TGT}', source='foo.txt', target='bar.txt')
	ctx(rule='../../bin/pyjscompile -o ${TGT} ${SRC}', source='test.py', target='test.js')


def dist(ctx):
	ctx.algo = 'zip'
	ctx.excl = '**/.waf* **/*~ **/*.pyc **/*.swp **/.lock-w*'


def examples(ctx):
	print('hello from %s!' % (type(ctx.path),))
	ctx.recurse('doc')


class _build(BuildContext):
	cmd = 'build'
	variant = 'default'

# vim: :set noexpandtab:
