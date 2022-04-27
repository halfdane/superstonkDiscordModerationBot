from redditItemHandler.flairy import Flairy

flairy = Flairy(None)

def match(string, expected1, expected2):
    m = flairy._flairy_detect_user_flair_change.match(string)

    print(m.group(1))
    print(m.group(2))

    if expected1:
        assert m.group(1).strip() == expected1

        if expected2:
            assert m.group(2).strip() == expected2
        else:
            assert m.group(2) is None
    else:
        assert m is None


def test_multiline():
    match(">\n      >\n >"
               "!Flairy! king gizzard and the lizard wizard 🚀 "
               "red  \n  whatever  ￼\n   neyy ", "king gizzard and the lizard wizard 🚀", "red")

def test_whitespace_variations():
    match("!Flairy! something ", "something", None)
    match("!Flairy! something", "something", None)
    match("!Flairy!something ", "something", None)
    match("!Flairy!something", "something", None)

    match("!Flairy!  something  red  ", "something", "red")
    match("!Flairy!something  red  ", "something", "red")
    match("!Flairy!  something red  ", "something", "red")
    match("!Flairy!  something  red", "something", "red")

    match("!Flairy!something red  ", "something", "red")
    match("!Flairy!something  red", "something", "red")

    match("!Flairy!  something   red   ", "something", "red")
    match("!Flairy!something   red   ", "something", "red")
    match("!Flairy!  something red   ", "something", "red")
    match("!Flairy!  something   red ", "something", "red")

    match("!Flairy!something red   ", "something", "red")
    match("!Flairy!something   red ", "something", "red")
    match("!Flairy!something red ", "something", "red")

    match("! FLAIRY ! Lotion in the basket ✅", "Lotion in the basket ✅", None)


def test_valid_colors():
    match("!Flairy!  something   red   ", "something", "red")
    match("!Flairy!  something   blue   ", "something", "blue")
    match("!Flairy!  something   pink   ", "something", "pink")
    match("!Flairy!  something   yellow   ", "something", "yellow")
    match("!Flairy!  something   green   ", "something", "green")
    match("!Flairy!  something   black   ", "something", "black")


def test_invalid_colors():
    match("!Flairy!  something   violet   ", "something   violet", None)
    match("!Flairy!  something coral   ", "something coral", None)
    match("!Flairy!  something sparkle   ", "something sparkle", None)
    match("!Flairy!  something purple   ", "something purple", None)


