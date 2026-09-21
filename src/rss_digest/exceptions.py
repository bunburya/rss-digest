"""Commonly used custom exception classes."""


class RSSDigestError(Exception):
    """Base class for all errors."""
    pass


class BadInstallationError(RSSDigestError):
    """App is not installed properly."""
    pass


class ProfileError(RSSDigestError):
    """Base class for profile-related errors."""
    pass


class ProfileNotFoundError(ProfileError):
    """The specified profile cannot be loaded."""
    pass


class ProfileExistsError(ProfileError):
    """An attempt has been made to create a profile that already exists."""
    pass


class FeedError(RSSDigestError):
    """Base class for all errors relating to adding or fetching feeds."""
    pass


class OPMLError(FeedError):
    """Base type for OPML-related errors."""
    pass


class OPMLNotFoundError(OPMLError):
    """An OPML file cannot be found."""
    pass


class BadOPMLError(OPMLError):
    """An OPML file is not valid."""
    pass


class FeedNotFoundError(FeedError):
    """A particular feed cannot be found."""
    pass


class CategoryExistsError(FeedError):
    """Attempted to create a new feed category but a category with that
    name already exists.
    """
    pass


class FeedExistsError(FeedError):
    """Attempted to add a new feed but that feed already exists."""
    pass


class BadConfigurationError(RSSDigestError):
    """Some relevant value has not been configured properly."""
    pass
