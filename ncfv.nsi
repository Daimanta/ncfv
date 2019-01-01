; This is a NSIS installer script.  See http://nsis.sourceforge.net/

!define VER 0.1
!define PYTHONDLL python24.dll

Name "ncfv"

Outfile "ncfv-${VER}.exe"

; usa LZMA (7zip) compression, about 20% smaller
SetCompressor lzma

; The default installation directory
InstallDir $PROGRAMFILES\ncfv

ShowInstDetails show
;hmm
ShowUninstDetails show

; The text to prompt the user to choose components
ComponentText "This will install ncfv ${VER} onto your computer.  For typical usage you will want ncfv available in your PATH.  Therefore, it is recommended that you choose the option to create a ncfv.bat in your windows directory."

; The text to prompt the user to enter a directory
DirText "Choose a directory to install in to:"


Section "exe and support files (required)"
  SectionIn RO

  SetOutPath $INSTDIR

  File dist\ncfv.exe
  File dist\library.zip
  File dist\*.pyd
  File dist\${PYTHONDLL}

  ; Write the installation path into the registry
  ;WriteRegStr HKLM SOFTWARE\ncfv "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ncfv" "DisplayName" "ncfv ${VER} (remove only)"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ncfv" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteUninstaller "uninstall.exe"

SectionEnd


Section "documentation"
  SetOutPath $INSTDIR

  File ncfv.txt
  File Changelog.txt
  File COPYING.txt

SectionEnd


Section "$WINDIR\ncfv.bat file"
  DetailPrint "Creating batch file: $WINDIR\ncfv.bat"

  FileOpen $1 $WINDIR\ncfv.bat w
  FileWrite $1 "@echo off$\r$\n" 
  FileWrite $1 "$\"" 
  FileWrite $1 $INSTDIR
  FileWrite $1 "\ncfv.exe$\" "

  ; we want to use %* in the .bat file, but it doesn't exist on win 9x/ME
  ReadRegStr $2 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" CurrentVersion
  IfErrors 0 lbl_winnt
  ; we are not NT.
  FileWrite $1 "%1 %2 %3 %4 %5 %6 %7 %8 %9$\r$\n"
  Goto lbl_done
lbl_winnt:
  FileWrite $1 "%*$\r$\n"
lbl_done:

  FileClose $1
SectionEnd


;--------------------------------

; Uninstaller

UninstallText "This will remove ncfv from your computer. Hit the uninstall button if you wish to continue."

; Uninstall section

Section "Uninstall"
  
  ; remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\ncfv"
  ;DeleteRegKey HKLM SOFTWARE\ncfv

  ; remove files
  Delete $INSTDIR\ncfv.exe
  Delete $INSTDIR\library.zip
  Delete $INSTDIR\${PYTHONDLL}
  Delete $INSTDIR\*.pyd
  
  Delete $INSTDIR\ncfv.txt
  Delete $INSTDIR\Changelog.txt
  Delete $INSTDIR\COPYING.txt
  
  ; remove generated .bat file
  Delete $WINDIR\ncfv.bat
  
  ; remove uninstaller
  Delete $INSTDIR\uninstall.exe

  ; remove shortcuts, if any
  ;Delete "$SMPROGRAMS\ncfv\*.*"

  ; remove directories used
  ;RMDir "$SMPROGRAMS\ncfv"
  RMDir "$INSTDIR"

SectionEnd

