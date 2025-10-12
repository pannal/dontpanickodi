# skin.plextuary

_An Estuary fork with PM4K optimizations_

## Notes
The biggest impact this 99.9%-like-Estuary skin has is that it doesn't show the massive black backdrop-shadow when PM4K's player is paused. Also it enables the UI to hide faster.

There are some feature additions as well, though, and we have specific builds for CoreELEC and CoreELEC CPM, with more detailed PlayerProcessInfo implementations.

### Custom Exit Menu
Plextuary will read includes from `.kodi/addons/ExitMenuAdd.xml` or `.kodi/addons/ExitMenuReplacement.xml`. With the latter completely replacing the supplied Exit Kodi menu with the contents of the XML.

When you want to use `.kodi/addons/ExitMenuReplacement.xml` (only available with Kodi Nexus (20) or above), this skin requires the `script.skinvariables` (Skin Variables) plugin to be installed.

For anything below Nexus (Skin Variables wasn't mature enough, yet), or without Skin Variables installed, only `ExitMenuAdd.xml` is considered.

Layout of `ExitMenuAdd.xml`:
```
<?xml version="1.0" encoding="UTF-8"?>
<includes>
    <include name="ExitMenuAdd">
        <item>
            <label>Additional Menu Item!</label>
            <onclick>Meep</onclick>
        </item>
</include>
</includes>
```

Layout of `ExitMenuReplacement.xml`:
```
<?xml version="1.0" encoding="UTF-8"?>
<includes>
    <include name="ExitMenuReplacement">
        <item>
            <label>Menu Item 1!</label>
            <onclick>Meep</onclick>
        </item>
        <item>
            <label>Menu Item 2!</label>
            <onclick>Meep</onclick>
        </item>
    </include>
</includes>
```