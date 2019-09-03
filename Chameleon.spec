# -*- mode: python -*-

block_cipher = None

added_files = [
                ('chameleon/OSMtag.yaml', 'data'),
                ('resources/chameleon.png', '.'),
                ('resources/chameleon.icns', '.')
             ]

a = Analysis(['chameleon/main.py'],
             pathex=['/Users/primaryuser/chameleon-2'],
             binaries=[],
             datas= added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Chameleon',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='resources/chameleon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Chameleon')
app = BUNDLE(coll,
             name='Chameleon.app',
             icon='resources/chameleon.icns',
             bundle_identifier=None,
             info_plist={
            'NSHighResolutionCapable': 'True',
            'NSRequiresAquaSystemAppearance': 'False'
            },
        )
