@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build

if "%1" == "" goto help

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.https://sphinx-doc.org/
	exit /b 1
)

if "%1" == "install" goto install
if "%1" == "clean" goto clean
if "%1" == "livehtml" goto livehtml
if "%1" == "apidoc" goto apidoc
if "%1" == "rebuild" goto rebuild

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:help
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:install
pip install -r requirements.txt
goto end

:clean
rmdir /s /q %BUILDDIR%
goto end

:livehtml
sphinx-autobuild -b html %SPHINXOPTS% %SOURCEDIR% %BUILDDIR%\html --host 0.0.0.0 --port 8000
goto end

:apidoc
sphinx-apidoc -o api ..\src --force --separate --module-first
goto end

:rebuild
call :clean
call :apidoc
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:end
popd