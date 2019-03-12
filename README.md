# Mupi Question Database

A REST database with questions and answers.

## Pre requisites

Before installing, you need some softwares:

* Virtual Environment
* Pip
* Python3

  ```bash
  $ sudo apt-get install pip virtualenv git build-essential python3-dev gettext
  ```

* PostgresSQL >= 9.5

  ```bash
  $ sudo apt-get install postgresql-server-dev-all postgres
  ```

* Some libraries

  ```bash
  $ sudo apt-get install libcurl4-openssl-dev libssl-dev
  ```

## Instalation

### Database

You will need a Postgres database called **masteraula**, or other in your preference. If you are going to use another name, you need to remember to change it in settings file.

```bash
$ createdb --encoding "UTF-8" masteraula
```

### Virtual Environment

You will need an virtual Environment to controll the python dependencies and libraries. Just remember to create a Virtual Environment for **python 3**.

```bash
$ virtualenv env -p python3
```

Then you can activate it to install the libraries requirements.

```bash
$ source env/bin/activate
```
On Windows:
```bash
$ . env/Scripts/activate
```
Then
```bash
$ pip install -r requirements/local.txt
$ pip install celery[sqs]
```

If some error appear, consider installing the python 3 developer libraries 

```bash
$ sudo apt-get install python3-dev
```
Windows has a known error installing Pillow package. If this is your case, consider downloading specific Pillow wheel for your Windows and Python version at https://www.lfd.uci.edu/~gohlke/pythonlibs/#pillow an then run
```bash
$ pip install Pillow<your-version-here>.whl
```
After the installation run the previous `pip install` command again.
### Mupi question database

After cloning this repository, creating a databse and a virtual environment, it is time to run the migrations of the project.

But before, there is a **bug**, in the project (still figuring out) with the taggit library, this way it is not possible to migrate.

The bug occurs in `rest_views.py` at **TagListView** class in the `queryset = Question.tags.most_common()` line.

The workaround is going to `config/urls.py` and comment this line `url(r'^rest/', include('masteraula.questions.urls', namespace='rest')),`

Then it is now possible to run

```bash
$./manage.py migrate
```

After that, just uncomment the line that you commented to workaround the bug

### User

* To create an **superuser account**, use this command

```bash
$./manage.py createsuperuser
```

* To create a **normal user account**, you need to add it manually using the plataform.

  1. Run the server
  ```bash
  $./manage.py runserver
  ```
  2. Go to the registration rest page http://localhost:8000/rest/auth/registration/
  3. Fill the form and confirm
  4. An confirmation email will appear at the console, access this url to confirm the registration
