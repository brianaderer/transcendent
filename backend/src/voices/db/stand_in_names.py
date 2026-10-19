"""Stand-in usernames for the seed (atlas OPEN-37): the repo is public, so no real Reddit
username goes into its data file. Each user becomes `sailor-0001`, `sailor-0002`, … in the
order they first appear, and a post that names a user (`u/name`) names the same stand-in, so
the app can still tell people apart."""

import re

STAND_IN_FORMAT = "sailor-{:04d}"
# Reddit usernames are 3 to 20 letters, digits, underscores or hyphens; the look-behind
# keeps words that merely contain "u/" (menu/galley) from counting as a mention.
MENTION = re.compile(r"(?<![\w/])(/?u/)([A-Za-z0-9_-]{3,20})")


class StandInNames:
    """One export's stand-ins. Reddit treats usernames without regard to case, so this does."""

    def __init__(self) -> None:
        self._stand_ins: dict[str, str] = {}

    def name_for(self, username: str) -> str:
        key = username.lower()
        if key not in self._stand_ins:
            self._stand_ins[key] = STAND_IN_FORMAT.format(len(self._stand_ins) + 1)
        return self._stand_ins[key]

    def in_text(self, text: str) -> str:
        """The text with every mention of a user naming their stand-in instead."""
        return MENTION.sub(lambda found: found[1] + self.name_for(found[2]), text)
