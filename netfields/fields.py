from netaddr import IPAddress, IPNetwork, EUI

from django.db import models

from netfields.managers import NET_OPERATORS, NET_TEXT_OPERATORS
from netfields.forms import InetAddressFormField, CidrAddressFormField, MACAddressFormField
from netfields.mac import mac_unix_common


class _NetAddressField(models.Field):
    empty_strings_allowed = False

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = self.max_length
        super(_NetAddressField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value:
            return value

        return self.python_type()(value)

    def get_prep_lookup(self, lookup_type, value):
        if not value:
            return None

        if (lookup_type in NET_OPERATORS and
                NET_OPERATORS[lookup_type] not in NET_TEXT_OPERATORS):
            if lookup_type.startswith('net_contained') and value is not None:
                # Argument will be CIDR
                return unicode(value)
            return self.get_prep_value(value)

        return super(_NetAddressField, self).get_prep_lookup(
            lookup_type, value)

    def get_prep_value(self, value):
        if not value:
            return None

        return unicode(self.to_python(value))

    def get_db_prep_lookup(self, lookup_type, value, connection,
            prepared=False):
        if not value:
            return []

        if (lookup_type in NET_OPERATORS and
                NET_OPERATORS[lookup_type] not in NET_TEXT_OPERATORS):
            return [value] if prepared else [self.get_prep_value(value)]

        return super(_NetAddressField, self).get_db_prep_lookup(
            lookup_type, value, connection=connection, prepared=prepared)

    def formfield(self, **kwargs):
        defaults = {'form_class': self.form_class()}
        defaults.update(kwargs)
        return super(_NetAddressField, self).formfield(**defaults)



class InetAddressField(_NetAddressField):
    description = "PostgreSQL INET field"
    max_length = 39
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        return 'inet'

    def python_type(self):
        return IPAddress

    def form_class(self):
        return InetAddressFormField


class CidrAddressField(_NetAddressField):
    description = "PostgreSQL CIDR field"
    max_length = 43
    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        return 'cidr'

    def python_type(self):
        return IPNetwork

    def form_class(self):
        return CidrAddressFormField


class MACAddressField(models.Field):
    description = "PostgreSQL MACADDR field"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 17
        super(MACAddressField, self).__init__(*args, **kwargs)

    def db_type(self, connection):
        return 'macaddr'

    def to_python(self, value):
        if not value:
            return value

        return EUI(value, dialect=mac_unix_common)

    def get_prep_value(self, value):
        if not value:
            return None

        return unicode(self.to_python(value))

    def formfield(self, **kwargs):
        defaults = {'form_class': MACAddressFormField}
        defaults.update(kwargs)
        return super(MACAddressField, self).formfield(**defaults)

class IP4RField(_NetAddressField):
    description = "PostgreSQL ip4r extension ip4r type"
    max_length = len("255.255.255.255-255.255.255.255")
    __metaclas__ = models.SubfieldBase

    def db_type(self, connection):
        return 'ip4r'

    # Could convert to IPRange/IPNetwork/IPAddress here
    # instead of strings in a to_python() method.

    def get_prep_value(self, value):
        if not value:
            return None

        return unicode(value)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], [
        "^netfields\.fields\.InetAddressField",
        "^netfields\.fields\.CidrAddressField",
        "^netfields\.fields\.IP4RAddressField",
        "^netfields\.fields\.MACAddressField",
    ])
except ImportError:
    pass
