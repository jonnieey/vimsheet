@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "clean" goto clean
if "%1" == "html-strict" goto html-strict
if "%1" == "serve" goto serve
if "%1" == "check" goto check
if "%1" == "github" goto github
if "%1" == "offline" goto offline

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found.
	echo.
	exit /b 1
)

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:clean
rmdir /s /q %BUILDDIR% 2>NUL
rmdir /s /q %SOURCEDIR%\_autosummary 2>NUL
goto end

:html-strict
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR% -W --keep-going %O%
goto end

:serve
echo Starting documentation server at http://localhost:8000
python3 -m http.server 8000 --directory %BUILDDIR%\html
goto end

:check
%SPHINXBUILD% -M linkcheck %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
%SPHINXBUILD% -M doctest %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
%SPHINXBUILD% -M coverage %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
goto end

:github
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR%\github-pages %SPHINXOPTS% %O%
goto end

:offline
%SPHINXBUILD% -M html %SOURCEDIR% %BUILDDIR%\offline -A offline=True %SPHINXOPTS% %O%
%SPHINXBUILD% -M epub %SOURCEDIR% %BUILDDIR%\offline %SPHINXOPTS% %O%
goto end

:end
popd
