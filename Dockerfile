FROM ubuntu:16.04

RUN apt-get update -y
RUN apt-get install -y python-yaml python-jinja2 git
RUN apt-get install -y ansible 
COPY Ansible /home
CMD [ "ansible-playbook", "--version" ]
CMD [ "git", "--version" ]
