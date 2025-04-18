import adsk.core
import os
import traceback
from ...lib import fusionAddInUtils as futil
from ... import config

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

#region

app = adsk.core.Application.get()
ui = app.userInterface
local_handlers = []

# Command configuration
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_compareBodies'
CMD_NAME = 'Compare Bodies'
CMD_DESCRIPTION = 'Compare two selected bodies by volume and surface area'
IS_PROMOTED = False

# UI configuration
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'CompareBodiesPanel'
PANEL_NAME = 'Compare Bodies'
POSITION_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = ''
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

#endregion

# =============================================================================
# EVENT HANDLERS
# =============================================================================

#region

def start():
    """Initialize the add-in."""
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_DESCRIPTION, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    if not workspace:
        ui.messageBox(f"Workspace '{WORKSPACE_ID}' not found.")
        return

    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    if not panel:
        panel = workspace.toolbarPanels.add(PANEL_ID, PANEL_NAME, POSITION_ID, False)
        futil.log(f"Panel created: {PANEL_NAME}")

    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED
    futil.log("Command added to panel")

def stop():
    """Clean up UI elements."""
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    if not workspace:
        return

    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    if not panel:
        return

    control = panel.controls.itemById(CMD_ID)
    if control:
        control.deleteMe()
        futil.log("Control removed")

    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()
        futil.log("Command definition removed")

def command_created(args):
    """Set up command inputs."""
    try:
        cmd = args.command
        inputs = cmd.commandInputs

        # Add body selection inputs
        inputs.addSelectionInput('body1', 'Body 1', 'Select first body').addSelectionFilter('Bodies')
        inputs.addSelectionInput('body2', 'Body 2', 'Select second body').addSelectionFilter('Bodies')
        
        # Add tolerance input
        tolerance_input = inputs.addFloatSpinnerCommandInput(
            'tolerance', 
            'Tolerance', 
            '',  # unitType
            0.001,  # min
            1.0,  # max
            0.001,  # spinStep
            0.001  # initialValue
        )

        futil.add_handler(cmd.execute, command_execute, local_handlers=local_handlers)
        futil.add_handler(cmd.destroy, command_destroy, local_handlers=local_handlers)
        futil.log("Command UI setup complete")

    except Exception as e:
        ui.messageBox(f'Command creation failed:\n{traceback.format_exc()}')

def command_destroy(args):
    """Clean up handlers."""
    global local_handlers
    local_handlers = []
    futil.log("Command destroyed")

def command_execute(args):
    """Execute comparison logic."""
    try:
        inputs = args.command.commandInputs
        
        # Get selected bodies
        body1 = inputs.itemById('body1').selection(0).entity
        body2 = inputs.itemById('body2').selection(0).entity
        
        # Validate inputs
        if not all(isinstance(b, adsk.fusion.BRepBody) for b in [body1, body2]):
            ui.messageBox("Please select two valid bodies")
            return

        # Get comparison tolerance
        tolerance = inputs.itemById('tolerance').value

        # Calculate properties
        vol1, area1 = body1.physicalProperties.volume, body1.physicalProperties.area
        vol2, area2 = body2.physicalProperties.volume, body2.physicalProperties.area

        # Prepare comparison results
        result = (f"Body 1 - Volume: {vol1:.4f} cm³, Area: {area1:.2f} cm²\n"
                 f"Body 2 - Volume: {vol2:.4f} cm³, Area: {area2:.2f} cm²\n\n")

        # Compare geometry
        if abs(vol1 - vol2) < tolerance:
            if (body1.faces.count == body2.faces.count and 
                body1.edges.count == body2.edges.count):
                result += "Bodies are identical in geometry and volume."
            else:
                result += "Volumes match but geometry differs."
        else:
            result += "Bodies differ in volume or structure."

        ui.messageBox(result)
        futil.log("Comparison completed")

    except Exception as e:
        ui.messageBox(f'Comparison error:\n{traceback.format_exc()}')

# =============================================================================

#endregion