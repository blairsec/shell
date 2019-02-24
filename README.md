# Shell Deployment
This is a basic web server for automatically deploying binaries to a shell server, intended for pwn problems on CTFs. It is designed for Ubuntu 16.04, but may work on other distros with or without modification. It should be run as root. Since it should only be accessible by trusted users anyway, there is no assurance of security (you could probably mess stuff up if you wanted to).

## Running
```
pipenv install
pipenv run sudo env SHELL_DEPLOY_SECRET=<authentication key> gunicorn deploy:app
```

## Use
To deploy a binary, POST a tar archive file to `/challenge` with the `Authorization` header set to whatever you set `SHELL_DEPLOY_SECRET` to.

The archive must contain a config.yml. An example file can be seen below.

```yaml
root: '/problems'
competition: '2019'
name: 'test'
files:
  - src: 'binary'
    dest: 'binary'
    mode: 2555
  - src: 'flag'
    dest: 'flag'
    mode: 440
  - src: 'source.c'
    dest: 'source.c'
    mode: 444
xinetd:
  port: 19010
  server: 'binary'
```

The binary will deployed at the path `<root>/<competition>/<name>/`. Files are copied from within the archive. For xinetd to work, you must have xinetd installed.