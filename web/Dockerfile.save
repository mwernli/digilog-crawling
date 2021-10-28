FROM ubuntu

MAINTAINER gerj@zhaw.ch

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y -qq apache2
RUN apt-get install -y -qq apache2-utils
RUN apt-get install -y libapache2-mod-wsgi-py3
RUN apt-get install -y python-dev
RUN apt-get clean

RUN apt-get install -y python3.7
RUN apt-get install -y python3-pip

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir /var/www/webApp

COPY webApp.conf /etc/apache2/sites-available/webApp.conf
RUN a2ensite webApp

COPY webapp.wsgi /var/www/webApp/webapp.wsgi
COPY webApp /var/www/webApp/webApp

RUN a2dissite 000-default.conf
RUN a2ensite webApp.conf

EXPOSE 80

WORKDIR /var/www/webApp

CMD ["apache2ctl", "-D", "FOREGROUND"]
