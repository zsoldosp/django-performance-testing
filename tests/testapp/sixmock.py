try:
    from unittest.mock import patch, Mock, PropertyMock, MagicMock  # noqa: E501
except ImportError:
    from mock import patch, Mock, PropertyMock, MagicMock  # noqa: F401
