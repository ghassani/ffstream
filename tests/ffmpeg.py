import pytest
from ffstream.ffmpeg import ArgumentContainer
from collections import OrderedDict

"""
test_argument_container_default
"""


def test_argument_container_default():
	args = ArgumentContainer()

	assert isinstance(args.global_args(), list)
	assert isinstance(args.input_args(), OrderedDict)
	assert isinstance(args.output_args(), OrderedDict)
	assert args.has_args() is False
	assert args.has_global_args() is False
	assert args.has_input_args() is False
	assert args.has_output_args() is False

	args = ArgumentContainer({
		'global': ['al', 'quds'],
		'input': {
			'foo': 'bar',
			'bin': 'baz'
		},
		'output': {
			'bin': 'baz',
			'foo': 'bar'
		}
	})

	assert args.has_global_args() is True

	assert 'al' in args.global_args()
	assert 'quds' in args.global_args()

	assert args.has_input_args() is True

	assert 'foo' in args.input_args()
	assert 'bin' in args.input_args()
	assert args.input_args()['foo'] == 'bar'
	assert args.input_args()['bin'] == 'baz'


	assert args.has_output_args() is True

	assert 'bin' in args.output_args()
	assert 'foo' in args.output_args()
	assert args.output_args()['bin'] == 'baz'
	assert args.output_args()['foo'] == 'bar'