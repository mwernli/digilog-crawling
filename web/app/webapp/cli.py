import os
import click

i18n_dir = './webapp/i18n/'


def register(app):
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass

    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language."""
        print(os.getcwd())
        if os.system('pybabel extract -F {}babel.cfg -k _l -o {}messages.pot .'.format(i18n_dir, i18n_dir)):
            raise RuntimeError('extract command failed')
        if os.system(
                'pybabel init -i {}messages.pot -d {}translations -l '.format(i18n_dir, i18n_dir) + lang):
            raise RuntimeError('init command failed')
        os.remove('{}messages.pot'.format(i18n_dir))

    @translate.command()
    def update():
        """Update all languages."""
        if os.system('pybabel extract -F {}babel.cfg -k _l -o {}messages.pot .'.format(i18n_dir, i18n_dir)):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i {}messages.pot -d {}translations'.format(i18n_dir, i18n_dir)):
            raise RuntimeError('update command failed')
        os.remove('{}messages.pot'.format(i18n_dir))

    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system('pybabel compile -d {}translations'.format(i18n_dir)):
            raise RuntimeError('compile command failed')
