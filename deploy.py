from falcon_multipart.middleware import MultipartMiddleware
import falcon
import tarfile
import os
import yaml
import shutil
import subprocess
import stat

def safe(tarinfo):
	return '..' not in tarinfo.name.split(os.sep) and tarinfo.name[0] != os.sep

class ChallengeLoader:
	def on_post(req, resp):
		if req.context['auth']:
			try:
				archive = req.get_param('challenge').file
			except AttributeError:
				resp.status = '400'
				return
			tar = tarfile.open(fileobj=archive)
			if os.path.exists('./challenge'): shutil.rmtree('./challenge')
			os.mkdir('challenge')
			tar.extractall(path='./challenge', members=filter(safe, tar.getmembers()))
			try: config = yaml.load(open('./challenge/config.yml'))
			except FileNotFoundError:
				resp.status = '400'
				return
			except yaml.YAMLError:
				resp.status = '400'
				return
			os.makedirs(os.path.join(config['root'], config['competition']), exist_ok=True)
			problemdir = os.path.abspath(os.path.join(config['root'], config['competition'], config['name']))
			subprocess.run(['chattr', '-R', '-i', problemdir])
			username = 'problem' + config['competition'] + '_' + config['name']
			subprocess.run(['userdel', '-r', username])
			subprocess.run(['useradd', '-s', '/sbin/nologin', '-m', '-d', problemdir, '-G', 'problems', username])
			os.chmod(problemdir, 0o000)
			mutable = []
			for file in config['files']:
				os.makedirs(os.path.join(problemdir, os.path.dirname(file['dest'])), exist_ok=True)
				shutil.copy2(os.path.join('./challenge', file['src']), os.path.join(problemdir, file['dest']))
				if file.get('immutable', True) == False: mutable.append(os.path.join(problemdir, file['dest']))
			subprocess.run(['chown', '-R', username + ':' + username, problemdir])
			for file in config['files']: os.chmod(os.path.join(problemdir, file['dest']), int(str(file['mode']), 8))
			os.chmod(problemdir, 0o755)
			subprocess.run(['chattr', '-R', '+i', problemdir])
			if 'xinetd' in config:
				xinetdconf = open(os.path.join('/etc/xinetd.d/', username), 'w')
				with open('xinetd.conf') as f:
					template = f.read()
				xinetdconf.write(template.format(username=username, port=config['xinetd']['port'], server=os.path.join(problemdir, config['xinetd']['server'])))
				xinetdconf.close()
			subprocess.run(['systemctl', 'reload', 'xinetd'])
			for file in mutable: subprocess.run(['chattr', '-R', '-i', file])
			print(config)
		else: resp.status = '401'

class AuthMiddleware(object):

	def __init__(self, secret):
		self.secret = secret

	def process_resource(self, req, resp, resource, params):
		req.context['auth'] = req.get_header('Authorization') == self.secret

app = falcon.API(middleware=[AuthMiddleware(os.environ['PWN_SECRET']), MultipartMiddleware()])
app.add_route('/challenge', ChallengeLoader)
