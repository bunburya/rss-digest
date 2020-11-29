"""Commonly used custom exception classes."""


class ProfileError(Exception):
    """Base class for profile-related errors."""
    pass


class ProfileNotFoundError(ProfileError):
    """The specified profile cannot be loaded."""
    pass


class ProfileExistsError(ProfileError):
    """An attempt has been made to create a profile that already exists."""
    pass


class OPMLError(Exception):
    """Base type for OPML-related errors."""
    pass


class OPMLNotFoundError(OPMLError):
    """An OPML file cannot be found."""
    pass


class BadOPMLError(OPMLError):
    """An OPML file is not valid."""
    pass


class FeedNotFoundError(Exception):
    """A particular feed cannot be found."""
    pass


class CategoryExistsError(Exception):
    """Attempted to create a new feed category but a category with that
    name already exists.
    """
    pass
