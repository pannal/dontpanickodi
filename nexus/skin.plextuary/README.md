# skin.plextuary

_An Estuary fork with PM4K optimizations_

## Notes
The biggest impact this 99.9%-like-Estuary skin has is that it doesn't show the massive black backdrop-shadow when PM4K's player is paused. Also it enables the UI to hide faster.

There are some feature additions as well, though, and we have specific builds for CoreELEC and CoreELEC CPM, with more detailed PlayerProcessInfo implementations.

### Custom Exit Menu
#### Kodi 20 and above
* Enable the skin setting "Exit Menu customization"
* Requires the `script.skinvariables` (Skin Variables) plugin to be installed (installation will be offered by Kodi once you visit the exit menu with the skin setting enabled) 
* Plextuary will read includes from `.kodi/addons/ExitMenuAdd.xml` or `.kodi/addons/ExitMenuReplacement.xml`. With the latter completely replacing the supplied Exit Kodi menu with the contents of the XML

#### Kodi 18 and 19
* Enable the skin setting "Exit Menu customization"
* Plextuary will read includes from `.kodi/addons/ExitMenuAdd.xml`

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