
# pyinstaller -y build/pyinstaller.spec
block_cipher = None
a = Analysis(['-m','oracle_lottery.ui.main_window'], pathex=[], binaries=[], datas=[('assets/*','assets')],
             hiddenimports=[], hookspath=[], runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='OracleLotteryPredictor',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=True,
          console=False, icon='assets/icon.png')
