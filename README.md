Подготавливает PDF для печати колод KeyForge. URL колоды задаётся в скрипте – переменная `URL_EXAMPLE`

Требования:
* Python 3
* `imagemagick` (используются команты `montage` и `convert`), можно задать полные пути к командам в скрипте – переменные `CONVERT_PATH` и `MONTAGE_PATH`
* карты лежат в папке `cards` рядом со скриптом (путь можно поменять в скрипте)
* все карты имеют размер 750 на 1050 пикселей (2.5" на 3.5" при 300 DPI)
* все карты лежат в отдельных файлах, имя каждой карты начинается с её номера, пример:

```
cards/001_Anger.jpg
cards/002_Barehanded.jpg
cards/003_Blood_Money.jpg
cards/004_Brothers_in_Battle.jpg
cards/005_Burn_the_Stockpile.jpg
cards/006_Champion’s_Challenge.jpg
cards/007_Coward’s_End.jpg
cards/008_Follow_the_Leader.jpg
cards/009_Lava_Ball.jpg
```
