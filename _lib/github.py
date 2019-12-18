import gc
import os

try:
    import urequests as requests
except ImportError:
    import requests

from util import exists, rmtree


class Repo:
    def __init__(self, url, api_token=None, username=None):
        # GitHub repo address
        self.repo_url = url
        self.api_token = api_token
        self.username = username
        self._cached = {}

    @property
    def api_url(self):
        return self.repo_url.replace('https://github.com',
                                     'https://api.github.com/repos')

    def get(self, url, force=False, cache=True, **kwargs):
        if not cache or force or url not in self._cached:
            headers = {}
            if self.api_token:
                headers['Authorization'] = 'token ' + self.api_token
            if self.username:
                headers['User-Agent'] = self.username
            headers.update(kwargs.pop('headers', {}))
            print('get:', url)
            response = requests.get(url, headers=headers, **kwargs)
            if not cache:
                if url in self._cached:
                    del self._cached[url]
                return response
            self._cached[url] = response
        return self._cached[url]

    def latest_version(self, force=False):
        # Request info about latest release (at least one release must be
        # published).
        response = self.get(self.api_url + '/releases/latest', force=force)

        # Tag associated with release.
        try:
            tag = response.json()['tag_name']
            return tag
        except Exception:
            raise RuntimeError('Error: `%s`' % response.json())

    def tag_contents(self, tag, path='', **kwargs):
        response = self.get(self.api_url + '/contents' + path + 
                            '?ref=refs/tags/' + tag, **kwargs)
        return response.json()

    def download(self, contents, root='', cache=False, verbose=False):
        downloaded = []
        for path in contents:
            if path['type'] == 'file':
                url = path['download_url'].replace('/refs/tags', '')
                if root and not exists(root):
                    print('mkdir: ' + root)
                    os.mkdir(root)
                output_path = (root + '/' + path['name']
                               if root else path['name'])
                if verbose:
                    print('download `%s`' % output_path)
                response = self.get(url, cache=cache)
                with open(output_path, 'w') as output:
                    output.write(response.text)
                downloaded.append(output_path)
            elif path['type'] == 'dir':
                response = self.get(path['_links']['self'], cache=cache)
                contents = response.json()
                downloaded += self.download(contents,
                                            root=(root + '/' if root else '')
                                            + '/' + path['name'])
            gc.collect()
        return downloaded
