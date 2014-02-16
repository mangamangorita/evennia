"""
ANSI - Gives colour to text.

Use the codes defined in ANSIPARSER in your text
to apply colour to text according to the ANSI standard.

Examples:
 This is %crRed text%cn and this is normal again.
 This is {rRed text{n and this is normal again.

Mostly you should not need to call parse_ansi() explicitly;
it is run by Evennia just before returning data to/from the
user.

"""
import re
from src.utils import utils
from src.utils.utils import to_str

# ANSI definitions

ANSI_BEEP = "\07"
ANSI_ESCAPE = "\033"
ANSI_NORMAL = "\033[0m"

ANSI_UNDERLINE = "\033[4m"
ANSI_HILITE = "\033[1m"
ANSI_BLINK = "\033[5m"
ANSI_INVERSE = "\033[7m"
ANSI_INV_HILITE = "\033[1;7m"
ANSI_INV_BLINK = "\033[7;5m"
ANSI_BLINK_HILITE = "\033[1;5m"
ANSI_INV_BLINK_HILITE = "\033[1;5;7m"

# Foreground colors
ANSI_BLACK = "\033[30m"
ANSI_RED = "\033[31m"
ANSI_GREEN = "\033[32m"
ANSI_YELLOW = "\033[33m"
ANSI_BLUE = "\033[34m"
ANSI_MAGENTA = "\033[35m"
ANSI_CYAN = "\033[36m"
ANSI_WHITE = "\033[37m"

# Background colors
ANSI_BACK_BLACK = "\033[40m"
ANSI_BACK_RED = "\033[41m"
ANSI_BACK_GREEN = "\033[42m"
ANSI_BACK_YELLOW = "\033[43m"
ANSI_BACK_BLUE = "\033[44m"
ANSI_BACK_MAGENTA = "\033[45m"
ANSI_BACK_CYAN = "\033[46m"
ANSI_BACK_WHITE = "\033[47m"

# Formatting Characters
ANSI_RETURN = "\r\n"
ANSI_TAB = "\t"
ANSI_SPACE = " "

# Escapes
ANSI_ESCAPES = ("{{", "%%", "\\\\")


def sub_meth(obj, function):
    """
    RegexObject.sub() allows for the 'repl' argument to be a function.
    However, it doesn't call bound methods correctly. This forces 'self'
    to be passed.
    """
    if isinstance(function, basestring):
        return function
    def wrapped(*args, **kwargs):
        return function(obj, *args, **kwargs)
    return wrapped


class ANSIParser(object):
    """
    A class that parses ansi markup
    to ANSI command sequences

    We also allow to escape colour codes
    by prepending with a \ for mux-style and xterm256,
    an extra { for Merc-style codes
    """

    def parse_rgb(self, rgbmatch):
        """
        This is a replacer method called by re.sub with the matched
        tag. It must return the correct ansi sequence.

        It checks self.do_xterm256 to determine if conversion
        to standard ansi should be done or not.
        """
        if not rgbmatch:
            return ""
        rgbtag = rgbmatch.groups()[0]

        background = rgbtag[0] == '['
        if background:
            red, green, blue = int(rgbtag[1]), int(rgbtag[2]), int(rgbtag[3])
        else:
            red, green, blue = int(rgbtag[0]), int(rgbtag[1]), int(rgbtag[2])

        if self.do_xterm256:
            colval = 16 + (red * 36) + (green * 6) + blue
            #print "RGB colours:", red, green, blue
            return "\033[%s8;5;%s%s%sm" % (3 + int(background), colval/100, (colval % 100)/10, colval%10)
        else:
            #print "ANSI convert:", red, green, blue
            # xterm256 not supported, convert the rgb value to ansi instead
            if red == green and red == blue and red < 2:
                if background:
                    return ANSI_BACK_BLACK
                elif red >= 1:
                    return ANSI_HILITE + ANSI_BLACK
                else:
                    return ANSI_NORMAL + ANSI_BLACK
            elif red == green and red == blue:
                if background:
                    return ANSI_BACK_WHITE
                elif red >= 4:
                    return ANSI_HILITE + ANSI_WHITE
                else:
                    return ANSI_NORMAL + ANSI_WHITE
            elif red > green and red > blue:
                if background:
                    return ANSI_BACK_RED
                elif red >= 3:
                    return ANSI_HILITE + ANSI_RED
                else:
                    return ANSI_NORMAL + ANSI_RED
            elif red == green and red > blue:
                if background:
                    return ANSI_BACK_YELLOW
                elif red >= 3:
                    return ANSI_HILITE + ANSI_YELLOW
                else:
                    return ANSI_NORMAL + ANSI_YELLOW
            elif red == blue and red > green:
                if background:
                    return ANSI_BACK_MAGENTA
                elif red >= 3:
                    return ANSI_HILITE + ANSI_MAGENTA
                else:
                    return ANSI_NORMAL + ANSI_MAGENTA
            elif green > blue:
                if background:
                    return ANSI_BACK_GREEN
                elif green >= 3:
                    return ANSI_HILITE + ANSI_GREEN
                else:
                    return ANSI_NORMAL + ANSI_GREEN
            elif green == blue:
                if background:
                    return ANSI_BACK_CYAN
                elif green >= 3:
                    return ANSI_HILITE + ANSI_CYAN
                else:
                    return ANSI_NORMAL + ANSI_CYAN
            else:    # mostly blue
                if background:
                    return ANSI_BACK_BLUE
                elif blue >= 3:
                    return ANSI_HILITE + ANSI_BLUE
                else:
                    return ANSI_NORMAL + ANSI_BLUE

    def parse_ansi(self, string, strip_ansi=False, xterm256=False):
        """
        Parses a string, subbing color codes according to
        the stored mapping.

        strip_ansi flag instead removes all ansi markup.

        """
        if hasattr(string, '_raw_string'):
            if strip_ansi:
                return string.clean()
            else:
                return string.raw()
        if not string:
            return ''
        self.do_xterm256 = xterm256
        string = utils.to_str(string)

        # go through all available mappings and translate them
        parts = self.ansi_escapes.split(string) + [" "]
        string = ""
        for part, sep in zip(parts[::2], parts[1::2]):
            for sub in self.ansi_sub:
                part = sub[0].sub(sub_meth(self, sub[1]), part)
            string += "%s%s" % (part, sep[0].strip())
        if strip_ansi:
            # remove all ansi codes (including those manually
            # inserted in string)
            string = self.ansi_regex.sub("", string)
        return string

    # MUX-style mappings %cr %cn etc

    mux_ansi_map = [
        # commented out by default; they (especially blink) are
        # potentially annoying
        (r'%cn', ANSI_NORMAL),
        (r'%ch', ANSI_HILITE),
        (r'%r', ANSI_RETURN),
        (r'%t', ANSI_TAB),
        (r'%b', ANSI_SPACE),
        #(r'%cf', ANSI_BLINK),
        #(r'%ci', ANSI_INVERSE),
        (r'%cr', ANSI_RED),
        (r'%cR', ANSI_BACK_RED),
        (r'%cg', ANSI_GREEN),
        (r'%cG', ANSI_BACK_GREEN),
        (r'%cy', ANSI_YELLOW),
        (r'%cY', ANSI_BACK_YELLOW),
        (r'%cb', ANSI_BLUE),
        (r'%cB', ANSI_BACK_BLUE),
        (r'%cm', ANSI_MAGENTA),
        (r'%cM', ANSI_BACK_MAGENTA),
        (r'%cc', ANSI_CYAN),
        (r'%cC', ANSI_BACK_CYAN),
        (r'%cw', ANSI_WHITE),
        (r'%cW', ANSI_BACK_WHITE),
        (r'%cx', ANSI_BLACK),
        (r'%cX', ANSI_BACK_BLACK)
        ]

    # Expanded mapping {r {n etc

    hilite = ANSI_HILITE
    normal = ANSI_NORMAL

    ext_ansi_map = [
        (r'{n', normal),                # reset
        (r'{/', ANSI_RETURN),          # line break
        (r'{-', ANSI_TAB),             # tab
        (r'{_', ANSI_SPACE),           # space
        (r'{\*', ANSI_INVERSE),        # invert
        (r'{\^', ANSI_BLINK),          # blinking text (very annoying and not supported by all clients)

        (r'{r', hilite + ANSI_RED),
        (r'{g', hilite + ANSI_GREEN),
        (r'{y', hilite + ANSI_YELLOW),
        (r'{b', hilite + ANSI_BLUE),
        (r'{m', hilite + ANSI_MAGENTA),
        (r'{c', hilite + ANSI_CYAN),
        (r'{w', hilite + ANSI_WHITE),  # pure white
        (r'{x', hilite + ANSI_BLACK),  # dark grey

        (r'{R', normal + ANSI_RED),
        (r'{G', normal + ANSI_GREEN),
        (r'{Y', normal + ANSI_YELLOW),
        (r'{B', normal + ANSI_BLUE),
        (r'{M', normal + ANSI_MAGENTA),
        (r'{C', normal + ANSI_CYAN),
        (r'{W', normal + ANSI_WHITE),  # light grey
        (r'{X', normal + ANSI_BLACK),  # pure black

        (r'{\[r', ANSI_BACK_RED),
        (r'{\[g', ANSI_BACK_GREEN),
        (r'{\[y', ANSI_BACK_YELLOW),
        (r'{\[b', ANSI_BACK_BLUE),
        (r'{\[m', ANSI_BACK_MAGENTA),
        (r'{\[c', ANSI_BACK_CYAN),
        (r'{\[w', ANSI_BACK_WHITE),    # light grey background
        (r'{\[x', ANSI_BACK_BLACK)     # pure black background
        ]

    # xterm256 {123, %c134,

    xterm256_map = [
        (r'%([0-5]{3})', parse_rgb),  # %123 - foreground colour
        (r'%(\[[0-5]{3})', parse_rgb),  # %-123 - background colour
        (r'{([0-5]{3})', parse_rgb),   # {123 - foreground colour
        (r'{(\[[0-5]{3})', parse_rgb)   # {-123 - background colour
        ]

    # obs - order matters here, we want to do the xterms first since
    # they collide with some of the other mappings otherwise.
    ansi_map = xterm256_map + mux_ansi_map + ext_ansi_map

    # prepare regex matching
    ansi_sub = [(re.compile(sub[0], re.DOTALL), sub[1])
                     for sub in ansi_map]

    # prepare matching ansi codes overall
    ansi_regex = re.compile("\033\[[0-9;]+m")

    # escapes - these double-chars will be replaced with a single
    # instance of each
    ansi_escapes = re.compile(r"(%s)" % "|".join(ANSI_ESCAPES), re.DOTALL)

ANSI_PARSER = ANSIParser()


#
# Access function
#

def parse_ansi(string, strip_ansi=False, parser=ANSI_PARSER, xterm256=False):
    """
    Parses a string, subbing color codes as needed.

    """
    return parser.parse_ansi(string, strip_ansi=strip_ansi, xterm256=xterm256)


def raw(string):
    """
    Escapes a string into a form which won't be colorized by the ansi parser.
    """
    return string.replace('{', '{{').replace('%', '%%')


def group(lst, n):
    for i in range(0, len(lst), n):
        val = lst[i:i+n]
        if len(val) == n:
            yield tuple(val)


def _spacing_preflight(func):
    """
    This wrapper function is used to do some preflight checks on functions used
    for padding ANSIStrings.
    """
    def wrapped(self, width, fillchar=None):
        if fillchar is None:
            fillchar = " "
        if (len(fillchar) != 1) or (not isinstance(fillchar, str)):
            raise TypeError("must be char, not %s" % type(fillchar))
        if not isinstance(width, int):
            raise TypeError("integer argument expected, got %s" % type(width))
        difference = width - len(self)
        if difference <= 0:
            return self
        return func(self, width, fillchar, difference)
    return wrapped


def _query_super(func_name):
    """
    Have the string class handle this with the cleaned string instead of
    ANSIString.
    """
    def wrapped(self, *args, **kwargs):
        return getattr(self.clean(), func_name)(*args, **kwargs)
    return wrapped


def _on_raw(func_name):
    """
    Like query_super, but makes the operation run on the raw string.
    """
    def wrapped(self, *args, **kwargs):
        args = list(args)
        try:
            string = args.pop(0)
            if hasattr(string, 'raw_string'):
                args.insert(0, string.raw())
            else:
                args.insert(0, string)
        except IndexError:
            pass
        result = _query_super(func_name)(self, *args, **kwargs)
        if isinstance(result, basestring):
            return ANSIString(result, decoded=True)
        return result
    return wrapped


def _transform(func_name):
    """
    Some string functions, like those manipulating capital letters,
    return a string the same length as the original. This function
    allows us to do the same, replacing all the non-coded characters
    with the resulting string.
    """
    def wrapped(self, *args, **kwargs):
        replacement_string = _query_super(func_name)(self, *args, **kwargs)
        to_string = []
        for index in range(0, len(self.raw_string)):
            if index in self._code_indexes:
                to_string.append(self.raw_string[index])
            elif index in self._char_indexes:
                to_string.append(replacement_string[index])
        return ANSIString(''.join(to_string), decoded=True)
    return wrapped

class ANSIMeta(type):
    """
    Many functions on ANSIString are just light wrappers around the unicode
    base class. We apply them here, as part of the classes construction.
    """
    def __init__(cls, *args, **kwargs):
        for func_name in [
                'count', 'startswith', 'endswith', 'find', 'index', 'isalnum',
                'isalpha', 'isdigit', 'islower', 'isspace', 'istitle', 'isupper',
                'rfind', 'rindex', '__len__']:
            setattr(cls, func_name, _query_super(func_name))
        for func_name in [
                '__mul__', '__mod__', 'expandtabs', '__rmul__', 'join',
                'decode', 'replace', 'format']:
            setattr(cls, func_name, _on_raw(func_name))
        for func_name in [
                'capitalize', 'translate', 'lower', 'upper', 'swapcase']:
            setattr(cls, func_name, _transform(func_name))
        super(ANSIMeta, cls).__init__(*args, **kwargs)


class ANSIString(unicode):
    """
    String-like object that is aware of ANSI codes.

    This isn't especially efficient, as it doesn't really have an
    understanding of what the codes mean in order to eliminate
    redundant characters. This could be made as an enhancement to ANSI_PARSER.

    If one is going to use ANSIString, one should generally avoid converting
    away from it until one is about to send information on the wire. This is
    because escape sequences in the string may otherwise already be decoded,
    and taken literally the second time around.

    Please refer to the Metaclass, ANSIMeta, which is used to apply wrappers
    for several of the methods that need not be defined directly here.
    """
    __metaclass__ = ANSIMeta

    def __new__(cls, *args, **kwargs):
        """
        When creating a new ANSIString, you may use a custom parser that has
        the same attributes as the standard one, and you may declare the
        string to be handled as already decoded. It is important not to double
        decode strings, as escapes can only be respected once.

        If the regexable flag is set, using __getitem__, such as when getting
        an index or slicing, will return the result from the raw string. If
        this flag is set False, it will intelligently skip ANSI escapes.

        ANSIString('{rHello{g, W{yorld', regexable=True)[0] will return the
        first byte of the escape sequence before 'Hello', while
        ANSIString('{rHello{g, W{yorld')[0] will return a red 'H'.

        When a regexable ANSIString is sliced, the result is returned as a
        non-regexable ANSI String. This ensures that usage of regexable
        ANSIStrings is an explicit choice.

        Why all this complication with the regexable flag?

        The reason is that while we are able to subclass the unicode object in
        Python, the byte representation of the string in memory cannot be
        changed and still exists under the hood. This doesn't matter for things
        coded in pure Python, but since Regexes need to be mindful of
        performance, the module that handles them operates directly on the
        memory representation of the string in order to do matching. It is thus
        completely unaware of our customizations to the class. Interestingly,
        however, while the re module does its matching on the raw string, it
        slices the string using the object's methods. This means that running
        a regex on an ANSIString would return matches at bogus indexes, since
        the __getitem__ method of ANSIString skips ANSI escape sequences, which
        were part of the raw data regex was matching against.

        So, if you need to use regex on an ANSIString, make sure you get it in
        regexable mode first, and be ready to deal with a few edge cases.
        """
        string = to_str(args[0], force_string=True)
        if not isinstance(string, basestring):
            string = str(string)
        parser = kwargs.get('parser', ANSI_PARSER)
        regexable = kwargs.get('regexable', False)
        decoded = kwargs.get('decoded', False) or hasattr(string, 'raw_string')
        if not decoded:
            string = parser.parse_ansi(string)
        if isinstance(string, unicode):
            string = super(ANSIString, cls).__new__(ANSIString, string)
        else:
            string = super(ANSIString, cls).__new__(ANSIString, string, 'utf-8')
        string._regexable = regexable
        return string

    def __repr__(self):
        """
        Let's make the repr the command that would actually be used to
        construct this object, for convenience and reference.
        """
        if self._regexable:
            reg = ', regexable=True'
        else:
            reg = ''
        return "ANSIString(%s, decoded=True%s)" % (repr(self._raw_string), reg)

    def __init__(self, *args, **kwargs):
        """
        When the ANSIString is first initialized, a few internal variables
        have to be set.

        The first is the parser. It is possible to replace Evennia's standard
        ANSI parser with one of your own syntax if you wish, so long as it
        implements the same interface.

        The second is the _raw_string. It should be noted that the ANSIStrings
        are unicode based. This seemed more reasonable than basing it off of
        the string class, because if someone were to use a unicode character,
        the benefits of knowing the indexes of the ANSI characters would be
        negated by the fact that a character within the string might require
        more than one byte to be represented. The raw string is, then, a
        unicode object rather than a true encoded string. If you need the
        encoded string for sending over the wire, try using the .encode()
        method.

        The third thing to set is the _clean_string. This is a unicode object
        that is devoid of all ANSI Escapes.

        Finally, _code_indexes and _char_indexes are defined. These are lookup
        tables for which characters in the raw string are related to ANSI
        escapes, and which are for the readable text.
        """
        self.parser = kwargs.pop('parser', ANSI_PARSER)
        super(ANSIString, self).__init__(*args, **kwargs)
        self._raw_string = unicode(self)
        self._clean_string = unicode(self.parser.parse_ansi(
            self._raw_string, strip_ansi=True), 'utf-8')
        self._code_indexes, self._char_indexes = self._get_indexes()

    def __add__(self, other):
        """
        We have to be careful when adding two strings not to reprocess things
        that don't need to be reprocessed, lest we end up with escapes being
        interpreted literally.
        """
        if not isinstance(other, basestring):
            return NotImplemented
        return ANSIString(self._raw_string + getattr(
            other, 'raw_string', other), decoded=True)

    def __radd__(self, other):
        """
        Likewise, if we're on the other end.
        """
        if not isinstance(other, basestring):
            return NotImplemented
        return ANSIString(getattr(
            other, 'raw_string', other) + self._raw_string, decoded=True)

    def __getslice__(self, i, j):
        """
        This function is deprecated, so we just make it call the proper
        function.
        """
        return self.__getitem__(slice(i, j))

    def _slice(self, slc):
        """
        This function takes a slice() object.

        Slices have to be handled specially. Not only are they able to specify
        a start and end with [x:y], but many forget that they can also specify
        an interval with [x:y:z]. As a result, not only do we have to track
        the ANSI Escapes that have played before the start of the slice, we
        must also replay any in these intervals, should the exist.

        Thankfully, slicing the _char_indexes table gives us the actual
        indexes that need slicing in the raw string. We can check between
        those indexes to figure out what escape characters need to be
        replayed.
        """
        slice_indexes = self._char_indexes[slc]
        if not slice_indexes:
            return ANSIString('')
        try:
            string = self[slc.start]._raw_string
        except IndexError:
            return ANSIString('')
        last_mark = slice_indexes[0]
        # Check between the slice intervals for escape sequences.
        for i in slice_indexes[1:]:
            for index in range(last_mark, i):
                if index in self._code_indexes:
                    string += self._raw_string[index]
            last_mark = i
            try:
                string += self._raw_string[i]
            except IndexError:
                pass
        return ANSIString(string, decoded=True)

    def __getitem__(self, item):
        """
        Gateway for slices and getting specific indexes in the ANSIString. If
        this is a regexable ANSIString, it will get the data from the raw
        string instead, bypassing ANSIString's intelligent escape skipping,
        for reasons explained in the __new__ method's docstring.
        """
        if self._regexable:
            return ANSIString(self._raw_string[item], decoded=True)
        if isinstance(item, slice):
            # Slices must be handled specially.
            return self._slice(item)
        try:
            item = self._char_indexes[item]
        except IndexError:
            raise IndexError("ANSIString index out of range.")

        clean = self._raw_string[item]
        result = ''
        # Get the character they're after, and replay all escape sequences
        # previous to it.
        for index in range(0, item + 1):
            if index in self._code_indexes:
                result += self._raw_string[index]
        return ANSIString(result + clean, decoded=True)

    def rsplit(self, sep=None, maxsplit=None):
        """
        Like split, but from the end of the string, rather than the beginning.
        """
        return self.split(sep, maxsplit, reverse=True)

    def split(self, sep=None, maxsplit=None, reverse=False):
        """
        Splits in a manner similar to the standard string split method. First,
        we split the clean string. Then we measure each section of the result
        to figure out where they start and end, and replay any escapes that
        would have occured before that.
        """
        if hasattr(sep, 'clean_string'):
            sep = sep.clean_string
        args = [sep]
        if maxsplit is not None:
            args.append(maxsplit)
        if reverse:
            parent_result = self._clean_string.rsplit(*args)
        else:
            parent_result = self._clean_string.split(*args)
        # Might be None.
        sep = sep or ''
        current_index = 0
        result = []
        for section in parent_result:
            result.append(self[current_index:current_index + len(section)])
            current_index += (len(section)) + len(sep)
        return result

    def clean(self):
        """
        Return a unicode object without the ANSI escapes.
        """
        return self._clean_string

    def raw(self):
        """
        Return a unicode object with the ANSI escapes.
        """
        return self._raw_string

    def is_regexable(self):
        """
        State whether or not this ANSIString is a 'regexable' ANSIString.
        Regexable ANSIStrings return indexes from _raw_string when sliced.
        """
        return self._regexable

    def regexable(self):
        """
        Return the regexable version of this ANSIString.
        """
        return ANSIString(self, decoded=True, regexable=True)

    def non_regexable(self):
        """
        Return the non-regexable version of this ANSIString.
        """
        return ANSIString(self, decoded=True)

    def partition(self, sep, reverse=False):
        """
        Similar to split, but always creates a tuple with three items:
        1. The part before the separator
        2. The separator itself.
        3. The part after.

        We use the same techniques we used in split() to make sure each are
        colored.
        """
        if hasattr(sep, '_clean_string'):
            sep = sep.clean()
        if reverse:
            parent_result = self._clean_string.rpartition(sep)
        else:
            parent_result = self._clean_string.partition(sep)
        current_index = 0
        result = tuple()
        for section in parent_result:
            result += (self[current_index:current_index + len(section)],)
            current_index += len(section)
        return result

    def _get_indexes(self):
        """
        Two tables need to be made, one which contains the indexes of all
        readable characters, and one which contains the indexes of all ANSI
        escapes. It's important to remember that ANSI escapes require more
        that one character at a time, though no readable character needs more
        than one character, since the unicode base class abstracts that away
        from us. However, several readable characters can be placed in a row.

        We must use regexes here to figure out where all the escape sequences
        are hiding in the string. Then we use the ranges of their starts and
        ends to create a final, comprehensive list of all indexes which are
        dedicated to code, and all dedicated to text.

        It's possible that only one of these tables is actually needed, the
        other assumed to be what isn't in the first.
        """
        matches = [
            (match.start(), match.end())
            for match in self.parser.ansi_regex.finditer(self._raw_string)]
        code_indexes = []
        # These are all the indexes which hold code characters.
        for start, end in matches:
            code_indexes.extend(range(start, end))

        if not code_indexes:
            # Plain string, no ANSI codes.
            return code_indexes, range(0, len(self._raw_string))
        flat_ranges = []
        # We need to get the ones between them, but the code might start at
        # the beginning, and there might be codes at the end.
        for tup in matches:
            flat_ranges.extend(tup)
        # Is the beginning of the string a code character?
        if flat_ranges[0] == 0:
            flat_ranges.pop(0)
        else:
            flat_ranges.insert(0, 0)
        # How about the end?
        end_index = (len(self._raw_string) - 1)
        if flat_ranges[-1] == end_index:
            flat_ranges.pop()
        else:
            flat_ranges.append(end_index)
        char_indexes = []
        for start, end in list(group(flat_ranges, 2)):
            char_indexes.extend(range(start, end))
        # The end character will be left off if it's a normal character. Fix
        # that here.
        if end_index in flat_ranges:
            char_indexes.append(end_index)
        return code_indexes, char_indexes

    @_spacing_preflight
    def center(self, width, fillchar, difference):
        """
        Center some text with some spaces padding both sides.
        """
        remainder = difference % 2
        difference /= 2
        spacing = difference * fillchar
        result = spacing + self + spacing + (remainder * fillchar)
        return result

    @_spacing_preflight
    def ljust(self, width, fillchar, difference):
        """
        Left justify some text.
        """
        return self + (difference * fillchar)

    @_spacing_preflight
    def rjust(self, width, fillchar, difference):
        """
        Right justify some text.
        """
        return (difference * fillchar) + self
