// Step type definitions; fields match 1:1 with backend/app/psadt/schema.py
export const STEP_TYPES = {
  welcome: { label: 'Welcome dialog / close apps', fields: [
    ['allow_defer', 'Allow deferral', 'bool'], ['defer_times', 'Number of deferrals', 'int'],
    ['check_disk_space', 'Check disk space', 'bool'], ['persist_prompt', 'Persist prompt', 'bool'],
    ['countdown', 'Close countdown (sec, 0 = off)', 'int']], defaults: { allow_defer: true, defer_times: 3, check_disk_space: true, persist_prompt: true, countdown: 0 } },
  progress: { label: 'Progress message', fields: [['message', 'Text (empty = default)', 'text']], defaults: { message: '' } },
  msi: { label: 'Run MSI', fields: [
    ['action', 'Action', ['Install', 'Uninstall', 'Repair', 'Patch']], ['file', 'MSI/MSP file', 'file'],
    ['product_code', 'Or ProductCode {GUID}', 'text'], ['transforms', 'Transform (.mst)', 'file'], ['args', 'Additional arguments ({Files} = Files folder)', 'text']],
    defaults: { action: 'Install', file: null, product_code: null, transforms: null, args: '' } },
  exe: { label: 'Run EXE', fields: [['file', 'File', 'file'], ['args', 'Arguments ({Files} = Files folder)', 'text'], ['ignore_exit_codes', 'Ignore exit codes (e.g. 1,2 or *)', 'text']],
    defaults: { file: '', args: '', ignore_exit_codes: '' } },
  uninstall_app: { label: 'Uninstall application by name', fields: [['name', 'Name', 'text'], ['name_match', 'Match', ['Contains', 'Exact', 'Wildcard', 'Regex']], ['args', 'Additional arguments ({Files} = Files folder)', 'text']],
    defaults: { name: '', name_match: 'Contains', args: '' } },
  registry: { label: 'Set registry value', fields: [['key', 'Key (HKLM\\...)', 'text'], ['name', 'Name', 'text'], ['value', 'Value', 'text'],
    ['value_type', 'Type', ['String', 'ExpandString', 'DWord', 'QWord', 'MultiString', 'Binary']]], defaults: { key: 'HKLM\\SOFTWARE\\', name: '', value: '', value_type: 'String' } },
  remove_registry: { label: 'Remove registry key/value', fields: [['key', 'Key', 'text'], ['name', 'Name (empty = whole key)', 'text']], defaults: { key: 'HKLM\\SOFTWARE\\', name: '' } },
  copy_file: { label: 'Copy file', fields: [['file', 'File', 'file'], ['destination', 'Destination folder', 'text']], defaults: { file: '', destination: '' } },
  remove_file: { label: 'Remove file', fields: [['path', 'Path', 'text']], defaults: { path: '' } },
  remove_folder: { label: 'Remove folder', fields: [['path', 'Path', 'text']], defaults: { path: '' } },
  custom: { label: 'Custom PowerShell', fields: [['code', 'Code (inserted into the script as is)', 'code']], defaults: { code: '' } },
}

export const PHASES = [['pre', 'Pre'], ['main', 'Main'], ['post', 'Post']]

export const DETECTION_TYPES = {
  msi: { label: 'MSI ProductCode', fields: [['product_code', 'ProductCode {GUID}'], ['min_version', 'Minimum version (optional)']], defaults: { product_code: '', min_version: '' } },
  file: { label: 'File', fields: [['path', 'Path (may contain %ProgramFiles%)'], ['min_version', 'Minimum file version (optional)']], defaults: { path: '', min_version: '' } },
  registry: { label: 'Registry', fields: [['key', 'Key (HKLM\\...)'], ['name', 'Value name (empty = key exists)'], ['value', 'Expected value (optional)']], defaults: { key: 'HKLM\\SOFTWARE\\', name: '', value: '' } },
}
