# ScriptToButton
Script To Button gives you the possibility to convert your Blender scripts into a button.
The add-on saves your scripts so that they can be used in any other Blender project.
You can also define properties for your script that allow you to use user input in your script.

# Installation 
1. Copy the url: `https://raw.githubusercontent.com/RivinHD/ScriptToButton/refs/heads/master/index.json`
2. Get Extensions → Repositories → [+] → Add Remote Repository
3. Enable `Check for Updates on Startup`
4. Install the extension by searching the `Available` list for `Script To Button` and click `Install`

# Legacy Installation
1. Go on the left side to [Release](https://github.com/RivinHD/ScriptToButton/releases/latest) and download the latest Version `legacy_script_to_button-2.3.2.zip` at the bottem under Assets.
1. Start Blender and navigate to Edit -> Preferences -> Add-ons and click "Install"
2. Select the Add-on named "ScriptToButton.zip" or "ScriptToButton-master.zip" and import it as .zip file
3. Enable the Add-on

# Usage
Go to the Sidebar. A tab named "Script To Button" is now available. (Also see [Wiki](https://github.com/RivinHD/ScriptToButton/wiki))

## "Controls" Panel
Here are control buttons for the Add-on located.

#### Add
Add a new Button to the "Buttons" Panel.
<br> When the button is pressed a popup will appear with options to name your button and to select the script from Texteditor which will be linked to the Button.

#### Remove
Remove the selected Button from the "Buttons" Panel.
<br> When the button is pressed a popup will appear with the options to delete the button from file and also the linked script.

#### Load
Give you the option to load all buttons from the Disk or from the Texteditor.
When the button is pressed a popup will appear with a switch to decide where to load from.
##### Load from Disk
A warning message is shown and when executed all buttons in Blender will be deleted and loaded from the disk.
##### Load from Texteditor
All Texts are represented with a checkbox to decide which to load.
<br> If the Button exist it will be reloaded otherwise a popup will appear with the option to add or skip this script.

#### Save 
(only available when Autostart is off)
<br> Save all buttons to the disk.

#### Load Button
Loads the selected Button into the Texteditor.

#### Reload
Reload the linked script of the selected button.
<br> If Autosave is active the button is also saved on the disk.

#### Edit
Give you the option to rename and remove properties of the selected button.
When the button is pressed a popup appear with a text field to put in the new name and a list of the properties.

#### Export
Opens an export window to export your buttons as .py files or one .zip file.
<br> On the right side of the export window are the option to choose in which format you want to export the scripts. Under this option, all buttons are listed with a checkbox to decide which ones to export.

#### Import
Opens an import window to import .py files or .zip files .
<br> You can select multiple .py and .zip files to import them all at once.

## "Buttons" Panel
All your buttons are displayed here

## "Properties" Panel
All registered properties of the selected button are displayed here

