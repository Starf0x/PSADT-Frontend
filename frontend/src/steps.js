// Definitie van de stap-types; velden komen 1-op-1 overeen met backend/app/psadt/schema.py
export const STEP_TYPES = {
  welcome: { label: 'Welkomstvenster / apps sluiten', fields: [
    ['allow_defer', 'Uitstel toestaan', 'bool'], ['defer_times', 'Aantal keer uitstellen', 'int'],
    ['check_disk_space', 'Schijfruimte controleren', 'bool'], ['persist_prompt', 'Venster blijft terugkomen', 'bool'],
    ['countdown', 'Aftellen voor sluiten (sec, 0 = uit)', 'int']], defaults: { allow_defer: true, defer_times: 3, check_disk_space: true, persist_prompt: true, countdown: 0 } },
  progress: { label: 'Voortgangsmelding', fields: [['message', 'Tekst (leeg = standaard)', 'text']], defaults: { message: '' } },
  msi: { label: 'MSI uitvoeren', fields: [
    ['action', 'Actie', ['Install', 'Uninstall', 'Repair', 'Patch']], ['file', 'MSI/MSP-bestand', 'file'],
    ['product_code', 'Of ProductCode {GUID}', 'text'], ['transforms', 'Transform (.mst)', 'file'], ['args', 'Extra argumenten', 'text']],
    defaults: { action: 'Install', file: null, product_code: null, transforms: null, args: '' } },
  exe: { label: 'EXE uitvoeren', fields: [['file', 'Bestand', 'file'], ['args', 'Argumenten', 'text'], ['ignore_exit_codes', 'Exitcodes negeren (bijv. 1,2 of *)', 'text']],
    defaults: { file: '', args: '', ignore_exit_codes: '' } },
  uninstall_app: { label: 'Applicatie verwijderen op naam', fields: [['name', 'Naam', 'text'], ['name_match', 'Vergelijking', ['Contains', 'Exact', 'Wildcard', 'Regex']], ['args', 'Extra argumenten', 'text']],
    defaults: { name: '', name_match: 'Contains', args: '' } },
  registry: { label: 'Registerwaarde instellen', fields: [['key', 'Sleutel (HKLM\\...)', 'text'], ['name', 'Naam', 'text'], ['value', 'Waarde', 'text'],
    ['value_type', 'Type', ['String', 'ExpandString', 'DWord', 'QWord', 'MultiString', 'Binary']]], defaults: { key: 'HKLM\\SOFTWARE\\', name: '', value: '', value_type: 'String' } },
  remove_registry: { label: 'Registersleutel/-waarde verwijderen', fields: [['key', 'Sleutel', 'text'], ['name', 'Naam (leeg = hele sleutel)', 'text']], defaults: { key: 'HKLM\\SOFTWARE\\', name: '' } },
  copy_file: { label: 'Bestand kopiëren', fields: [['file', 'Bestand', 'file'], ['destination', 'Doelmap', 'text']], defaults: { file: '', destination: '' } },
  remove_file: { label: 'Bestand verwijderen', fields: [['path', 'Pad', 'text']], defaults: { path: '' } },
  remove_folder: { label: 'Map verwijderen', fields: [['path', 'Pad', 'text']], defaults: { path: '' } },
  custom: { label: 'Eigen PowerShell', fields: [['code', 'Code (komt letterlijk in het script)', 'code']], defaults: { code: '' } },
}

export const PHASES = [['pre', 'Voor'], ['main', 'Hoofdactie'], ['post', 'Na']]

export const DETECTION_TYPES = {
  msi: { label: 'MSI ProductCode', fields: [['product_code', 'ProductCode {GUID}'], ['min_version', 'Minimale versie (optioneel)']], defaults: { product_code: '', min_version: '' } },
  file: { label: 'Bestand', fields: [['path', 'Pad (mag %ProgramFiles% bevatten)'], ['min_version', 'Minimale bestandsversie (optioneel)']], defaults: { path: '', min_version: '' } },
  registry: { label: 'Register', fields: [['key', 'Sleutel (HKLM\\...)'], ['name', 'Waardenaam (leeg = sleutel bestaat)'], ['value', 'Verwachte waarde (optioneel)']], defaults: { key: 'HKLM\\SOFTWARE\\', name: '', value: '' } },
}
