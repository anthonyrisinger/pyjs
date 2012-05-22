#!/usr/bin/env python
# encoding: utf-8


#from pprint import pprint as pp
from waflib.Build import BuildContext


APPNAME = 'pyjs'
VERSION = '0.8.1'


top = '.'
out = 'output'


def options(ctx):
	ctx.load('toolpyjs', tooldir='.')


def configure(ctx):
	ctx.load('toolpyjs', tooldir='.')


def build(ctx):
	ctx.load('toolpyjs', tooldir='.')
