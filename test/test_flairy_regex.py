from comments.flairy import Flairy


def EQUALS(x, y):
    return x == y


def NOT_EQUALS(x, y):
    return x != y


class TestFlairyRegex:
    testee = Flairy(None)

    def match(self, string, expected1, expected2=None, comparison=EQUALS):
        m = self.testee.flairy_detect_user_flair_change.match(string)

        if expected1:
            assert comparison(m.group(1), expected1)

            if expected2:
                assert comparison(m.group(2), expected2)
            else:
                assert comparison(m.group(2), None)
        else:
            assert comparison(m, None)

    def notmatch(self, string, expected1, expected2):
        m = self.testee.flairy_detect_user_flair_change.match(string)

        if expected1:
            assert m.group(1) == expected1

            if expected2:
                assert m.group(2) == expected2
            else:
                assert m.group(2) is None
        else:
            assert m is None

    def test_multiline(self):
        self.match(">\n      >\n >"
                   "!Flairy! king gizzard and the lizard wizard 🚀 "
                   "red  \n  whatever  ￼\n   neyy ", "king gizzard and the lizard wizard 🚀", "red")

    def test_whitespace_variations(self):
        self.match("!Flairy! something ", "something", None)
        self.match("!Flairy! something", "something", None)
        self.match("!Flairy!something ", "something", None)
        self.match("!Flairy!something", "something", None)

        self.match("!Flairy!  something  red  ", "something", "red")
        self.match("!Flairy!something  red  ", "something", "red")
        self.match("!Flairy!  something red  ", "something", "red")
        self.match("!Flairy!  something  red", "something", "red")

        self.match("!Flairy!something red  ", "something", "red")
        self.match("!Flairy!something  red", "something", "red")

        self.match("!Flairy!  something   red   ", "something", "red")
        self.match("!Flairy!something   red   ", "something", "red")
        self.match("!Flairy!  something red   ", "something", "red")
        self.match("!Flairy!  something   red ", "something", "red")

        self.match("!Flairy!something red   ", "something", "red")
        self.match("!Flairy!something   red ", "something", "red")
        self.match("!Flairy!something red ", "something", "red")

        self.match("! FLAIRY ! Lotion in the basket ✅", "Lotion in the basket ✅", None)

        self.match("!   Flairy!something red  ", "something", "red")
        self.match("!Flairy   ! something   red ", "something", "red")
        self.match("!   Flairy  !  something red ", "something", "red")

    def test_valid_colors(self):
        self.match("!Flairy!  something   red   ", "something", "red")
        self.match("!Flairy!  something   blue   ", "something", "blue")
        self.match("!Flairy!  something   pink   ", "something", "pink")
        self.match("!Flairy!  something   yellow   ", "something", "yellow")
        self.match("!Flairy!  something   green   ", "something", "green")
        self.match("!Flairy!  something   black   ", "something", "black")
        self.match("!FLAIRY!🍇🦧🏴‍☠️GrapeApe🏴‍☠️🍇🦧red", "🍇🦧🏴‍☠️GrapeApe🏴‍☠️🍇🦧", "red")

    def test_invalid_colors(self):
        self.match("!Flairy!  something   violet   ", "something   violet", None)
        self.match("!Flairy!  something coral   ", "something coral", None)
        self.match("!Flairy!  something sparkle   ", "something sparkle", None)
        self.match("!Flairy!  something purple   ", "something purple", None)

    def test_use_only_complete_word_as_color(self):
        self.match("!Flairy! ComputerShared", "ComputerSha", "red", NOT_EQUALS)
        self.match("!Flairy! ComputerShared", "ComputerShared", None)


