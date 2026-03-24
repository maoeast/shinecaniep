Option Explicit

' 创建所需对象
Dim WshShell, DesktopPath, ShortcutName, TargetExe, Arguments, IconPath, Shortcut
Dim FSO, ScriptPath, ScriptDir

Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' --- 动态获取脚本所在目录 ---
ScriptPath = WScript.ScriptFullName  ' 当前 VBScript 的完整路径
ScriptDir = FSO.GetParentFolderName(ScriptPath)  ' 提取所在目录

' --- 设置快捷方式属性 ---
ShortcutName = "资源教室管理系统-IEP"  ' 快捷方式名称
TargetExe = "C:\Users\Administrator\AppData\Roaming\360se6\Application\360se.exe"  ' 主程序路径
Arguments = "" & ScriptDir & "\index.html --start-maximized"  ' 动态拼接参数

' 图标路径（动态获取脚本目录下的 icon.ico）
IconPath = ScriptDir & "\icon.ico"  ' 使用脚本目录下的 icon.ico
If Not FSO.FileExists(IconPath) Then
    MsgBox "图标文件未找到: " & IconPath, vbExclamation, "警告"
    IconPath = TargetExe & ",0"  ' 回退到 Edge 默认图标
End If

' --- 创建快捷方式 ---
DesktopPath = WshShell.SpecialFolders("Desktop")  ' 获取桌面路径
Set Shortcut = WshShell.CreateShortcut(DesktopPath & "\" & ShortcutName & ".lnk")  ' 创建快捷方式

Shortcut.TargetPath = TargetExe       ' 设置目标主程序
Shortcut.Arguments = Arguments        ' 设置参数
Shortcut.IconLocation = IconPath      ' 设置图标（动态获取或回退）
Shortcut.Save                         ' 保存快捷方式

' 提示用户
MsgBox "快捷方式已创建在桌面上，名称为：" & ShortcutName & ".lnk", vbInformation, "完成"

' 释放对象
Set Shortcut = Nothing
Set WshShell = Nothing
Set FSO = Nothing
