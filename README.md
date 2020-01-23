## Preamble

Of the three methods to export messages from Windows Mobile, WP Message Backup is the last one continuing to work. Transfer my Data can only import messages between phones over Bluetooth - a Microsoft update removed the ability to create local backups. Another Microsoft app, Contacts+Messages Backup, constantly crashes. And unfortunately the XML output from WP Message Backup can be inaccurate, either due to the beta nature of that export format or the consistency of the OneDrive messaging store. Hence this script, normally run as:

```
$ ./wpmessagefixup messages.in.xml messages.out.xml -des -fs \
    -s PHONE_LANDLINE,PHONE_CELLULAR PHONE_LANDLINE,PHONE_CELLULAR ...
```

## Details:

* `-des`

  Delete empty SMS messages. Are they MMS control messages? No idea.

* `-fs`

  A small handful of MMS messages are incorrectly categorized, throwing errors during the Android import. Fix this.

* `-s`

  An incorrect phone number, such as a landline, may be selected if a contact has multiple numbers. Substitute the correct numbers back in. Watch out for country code prefixes!

The other options exist for edge cases that likely need not worry you.
