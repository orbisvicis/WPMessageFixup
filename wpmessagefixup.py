#!/usr/bin/env python3

import argparse
import xml.etree.ElementTree as ET
import base64
import magic
import mimetypes


def parent_child_iter(node, parent=None, tag=None):
    if tag is None or node.tag == tag:
        yield (parent,node)
    for child in node:
        yield from parent_child_iter(child, parent=node, tag=tag)


def fix_smil(mms):
    index = 0
    for part in mms.findall("./parts/part"):
        if part.get("ct") != "application/smil":
            continue
        if part.get("chset") not in ["","null",None]:
            continue
        data = part.get("data")
        if not data:
            continue
        try:
            data_dec = base64.b64decode(data)
        except ValueError:
            continue
        mime = magic.from_buffer(data_dec, mime=True)
        if not mime.startswith("image/"):
            continue
        fext = mimetypes.guess_extension(mime)
        if not fext:
            continue
        name = f"image{index:06}{fext}"
        part.set("ct", mime)
        part.set("chset", "null")
        part.set("cl", name)
        part.set("cid", f"<{name}>")
        index += 1


class NumberSubstitute(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        s = {"nargs","type"}
        if not s.isdisjoint(kwargs):
            message = f"Keywords {s} are not allowed"
            raise ValueError(message)
        super().__init__\
            ( option_strings, dest
            , nargs="+", type=self.number_tuple, **kwargs
            )

    @staticmethod
    def number_tuple(s):
        return tuple(i.strip() for i in s.split(","))

    def __call__(self, parser, namespace, v, option_string=None):
        try:
            i = namespace.__index
        except AttributeError:
            i = 0

        if len(v[0]) == 1:
            k = v[0][0]
            v = v[1:]
        else:
            k = None

        if not v:
            message = f"At least one comma-separated pair is required"
            raise argparse.ArgumentError(self, message)

        e = [i for i in v if len(i) != 2]

        if e:
            message = f"Arguments require exactly two comma-separated values: {e}"
            raise argparse.ArgumentTypeError(message)

        d = getattr(namespace, self.dest)
        d = {} if d is None else d
        l = d.setdefault(k, [])
        l.extend(enumerate(v, start=i))
        setattr(namespace, self.dest, d)

        namespace.__index = i + len(v)


parser = argparse.ArgumentParser\
    ( description="Fix 'WP Message Backup' Android XML Exports."
    )
parser.add_argument\
    ( "xml_in"
    , type=argparse.FileType("r", encoding="UTF-8")
    , help="Input XML file."
    )
parser.add_argument\
    ( "xml_out"
    , type=argparse.FileType("wb")
    , help="Output XML file."
    )
parser.add_argument\
    ( "-s", "--substitute"
    , default=dict()
    , action=NumberSubstitute
    , metavar=("[MessageIDMatch] NumberFrom,NumberTo", "NumberFrom,NumberTo")
    , help="Comma-separated number substitution pair. "
           "Applies to all messages unless limited by a given message ID. "
           "Substitution order is preserved and substitutions are not chained."
    )
parser.add_argument\
    ( "-n", "--current_number"
    , help="Current number."
    )
parser.add_argument\
    ( "-des", "--delete_empty_sms"
    , action="store_true"
    , help="Delete empty SMS messages."
    )
parser.add_argument\
    ( "-fs", "--fix_smil"
    , action="store_true"
    , help="Fix MMS SMIL data"
    )

args = parser.parse_args()

xml = ET.parse(args.xml_in)

args.xml_in.close()


for mms in xml.iter("mms"):
    mms_address = []
    mms_sender = False

    mms_mid = mms.get("m_id")

    subs = args.substitute.get(None, [])

    if mms_mid:
        subs_mid = args.substitute.get(mms_mid, [])
    else:
        subs_mid = []

    if subs_mid:
        subs = subs + subs_mid
        subs.sort()

    if mms.get("sub") == "0":
        mms.set("sub", "null")

    for addr in mms.findall("./addrs/addr"):
        addr_address = addr.get("address")
        addr_type = addr.get("type")

        if addr_address is None or addr_type is None:
            continue

        for (_,pair) in subs:
            if pair[0] == addr_address:
                addr_address = pair[1]
                break

        if addr_address in ["insert-address-token", args.current_number]:
            if addr_type == "137":
                mms_sender = True
        else:
            mms_address.append(addr_address)

        addr.set("address", addr_address)

    if mms_sender:
        mms.set("msg_box", "2")

    mms.set("address", "~".join(mms_address))

    if args.fix_smil:
        fix_smil(mms)


for sms in xml.iter("sms"):
    address = sms.get("address")

    if address is None:
        continue

    subs = args.substitute.get(None, [])

    for (_,pair) in subs:
        if pair[0] == address:
            address = pair[1]
            break

    sms.set("address", address)


if args.delete_empty_sms:
    empty = []

    for (sms_parent,sms) in parent_child_iter(xml.getroot(), tag="sms"):
        body = sms.get("body")

        if not body:
            empty.append((sms_parent,sms))

    for (sms_parent,sms) in empty:
        if sms_parent is None:
            continue

        sms_parent.remove(sms)


xml.write(args.xml_out)

args.xml_out.close()
