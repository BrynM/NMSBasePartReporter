import configargparse
import re
import shutil
import textwrap
from operator import attrgetter
from natsort import natsorted, ns

'''
		parser_config = configargparse.ArgParser(
			prog=os.path.basename(__file__),
			usage=None,
			formatter_class=ProperHelpFormatter,
		)
'''
help_formatter_override_width = None

class ProperHelpFormatter(configargparse.RawDescriptionHelpFormatter):
	paragraph_edge = re.compile(r"(\n\s*\n)", re.MULTILINE)
	class _Section(configargparse.RawDescriptionHelpFormatter._Section):
		def format_help(self):
			if self.parent is not None:
				self.formatter._indent()
			join = self.formatter._join_parts
			item_help = join([func(*args) for func, args in self.items])
			if self.parent is not None:
				self.formatter._dedent()
			if not item_help:
				return ''
			if self.heading is not configargparse.SUPPRESS and self.heading is not None:
				current_indent = self.formatter._current_indent
				heading = '%*s%s:\n' % (current_indent, '', self.heading[0].upper() + self.heading[1:])
			else:
				heading = ''
			return join(['\n', heading, item_help, '\n'])
	def __init__(
		self,
		prog,
		indent_increment=2,
		max_help_position=24,
		width=None
	):
		if not help_formatter_override_width is None:
			width = help_formatter_override_width
		if width is None:
			width = shutil.get_terminal_size().columns
			width -= 2
		self._prog = prog
		self._indent_increment = indent_increment
		self._original_max_help_position = max_help_position
		self._max_help_position = min(max_help_position, max(width - 20, indent_increment * 2))
		self._width = width
		self._current_indent = 0
		self._level = 0
		self._action_max_length = 0
		self._root_section = self._Section(self, None)
		self._current_section = self._root_section
		self._whitespace_matcher = re.compile(r'\s+', re.ASCII)
		self._long_break_matcher = re.compile(r'\n\n\n+')
	def add_arguments(self, actions):
		actions = natsorted(actions, key=attrgetter('option_strings'), alg=ns.IGNORECASE)
		super(ProperHelpFormatter, self).add_arguments(actions)
	def add_usage(self, usage, actions, groups, prefix="Usage:\n"):
		if usage is not configargparse.SUPPRESS:
			args = usage, actions, groups, prefix + (' ' * self._indent_increment)
			self._add_item(self._format_usage, args)
	def set_width(self, width: int=None):
		if width > 0:
			global help_formatter_override_width
			help_formatter_override_width = width
		else:
			help_formatter_override_width = None
		return help_formatter_override_width
	def _fill_text(self, text, width, indent):
		paragraphs = self.paragraph_edge.split(text)
		for paranum in range(0, len(paragraphs)):
			found_heading = re.search('^([^:]+:\n)', paragraphs[paranum], flags=re.MULTILINE)
			heading = ''
			if found_heading:
				heading = found_heading.group(1)
				paragraphs[paranum] = re.sub(re.escape(heading), '', paragraphs[paranum])
				paragraphs[paranum] = (' ' * self._indent_increment) + paragraphs[paranum]
			else:
				paragraphs[paranum] = (' ' * self._indent_increment) + paragraphs[paranum]
			paragraphs[paranum] = heading + textwrap.fill(
				paragraphs[paranum],
				width,
				initial_indent=indent,
				subsequent_indent=indent,
				replace_whitespace=False,
			)
		return "\n".join(paragraphs)
	def _format_action(self, action):
		help_position = min(self._action_max_length + 2, self._max_help_position)
		help_width = max(self._width - help_position, 11)
		action_width = help_position - self._current_indent - 2
		action_header = self._format_action_invocation(action)
		if not action.help:
			tup = self._current_indent, '', action_header
			action_header = '%*s%s\n' % tup
		else:
			tup = self._current_indent, '', action_header
			action_header = '%*s%s\n' % tup
			indent_first = help_position
		parts = [action_header]
		if action.help:
			help_text = self._expand_help(action)
			help_lines = self._split_lines(help_text, help_width)
			#termcols
			for line in help_lines:
				parts.append('%*s%s\n' % (help_position, '', line))
		elif not action_header.endswith('\n'):
			parts.append('\n')
		for subaction in self._iter_indented_subactions(action):
			parts.append(self._format_action(subaction))
		return self._join_parts(parts)
	def _get_help_string(self, action):
		help = action.help
		help = help[0].upper() + help[1:]
		if '%(default)' not in action.help:
			if action.default is not configargparse.SUPPRESS:
				defaulting_nargs = [configargparse.OPTIONAL, configargparse.ZERO_OR_MORE]
				if action.option_strings or action.nargs in defaulting_nargs:
					help += ' (Default: "%(default)s")'
		return help

