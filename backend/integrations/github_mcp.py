"""
GitHub MCP Integration
Repositórios, Issues e Pull Requests para OpenSlap
"""

from typing import Dict, Any, List, Optional
import aiohttp
import json
import base64

class GitHubMCP:
    """
    GitHub MCP - Repositórios, Issues e Pull Requests
    
    Funcionalidades:
    - Gestão de repositórios
    - Issues e milestones
    - Pull requests
    - Code review
    - Commits e branches
    - Actions/workflows
    - Releases
    - Search
    """
    
    def __init__(self, token: str, owner: str = None):
        self.token = token
        self.owner = owner
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None,
                           params: Dict = None) -> Dict[str, Any]:
        """Faz requisição à API do GitHub"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params
            ) as response:
                if response.status in [200, 201, 204]:
                    if response.status == 204:
                        return {"success": True}
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"GitHub API Error {response.status}: {error_text}")
    
    # ========== REPOSITÓRIOS ==========
    
    async def list_repositories(self, owner: str = None, type: str = "all",
                               sort: str = "updated", per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista repositórios"""
        target = owner or self.owner or "user"
        endpoint = f"/users/{target}/repos" if target != "user" else "/user/repos"
        
        return await self._make_request("GET", endpoint, params={
            "type": type,
            "sort": sort,
            "per_page": per_page
        })
    
    async def get_repository(self, repo: str, owner: str = None) -> Dict[str, Any]:
        """Obtém informações de um repositório"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}"
        return await self._make_request("GET", endpoint)
    
    async def create_repository(self, name: str, description: str = None,
                               private: bool = False, auto_init: bool = False) -> Dict[str, Any]:
        """Cria novo repositório"""
        endpoint = "/user/repos"
        data = {
            "name": name,
            "private": private,
            "auto_init": auto_init
        }
        if description:
            data["description"] = description
        return await self._make_request("POST", endpoint, data)
    
    async def delete_repository(self, repo: str, owner: str = None) -> bool:
        """Remove um repositório"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}"
        try:
            await self._make_request("DELETE", endpoint)
            return True
        except:
            return False
    
    # ========== ISSUES ==========
    
    async def list_issues(self, repo: str, owner: str = None, state: str = "open",
                         labels: str = None, assignee: str = None,
                         per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista issues de um repositório"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/issues"
        
        params = {"state": state, "per_page": per_page}
        if labels:
            params["labels"] = labels
        if assignee:
            params["assignee"] = assignee
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def create_issue(self, repo: str, title: str, body: str = None,
                          labels: List[str] = None, assignees: List[str] = None,
                          owner: str = None, milestone: int = None) -> Dict[str, Any]:
        """Cria nova issue"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/issues"
        
        data = {"title": title}
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        if assignees:
            data["assignees"] = assignees
        if milestone:
            data["milestone"] = milestone
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_issue(self, repo: str, issue_number: int, owner: str = None) -> Dict[str, Any]:
        """Obtém detalhes de uma issue"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/issues/{issue_number}"
        return await self._make_request("GET", endpoint)
    
    async def update_issue(self, repo: str, issue_number: int,
                          title: str = None, body: str = None,
                          state: str = None, labels: List[str] = None,
                          owner: str = None) -> Dict[str, Any]:
        """Atualiza uma issue"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/issues/{issue_number}"
        
        data = {}
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        if state:
            data["state"] = state
        if labels:
            data["labels"] = labels
        
        return await self._make_request("PATCH", endpoint, data)
    
    async def add_issue_comment(self, repo: str, issue_number: int,
                               body: str, owner: str = None) -> Dict[str, Any]:
        """Adiciona comentário a uma issue"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/issues/{issue_number}/comments"
        return await self._make_request("POST", endpoint, {"body": body})
    
    # ========== PULL REQUESTS ==========
    
    async def list_pull_requests(self, repo: str, owner: str = None,
                                  state: str = "open",
                                  per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista pull requests"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls"
        return await self._make_request("GET", endpoint, params={
            "state": state,
            "per_page": per_page
        })
    
    async def create_pull_request(self, repo: str, title: str, head: str,
                                 base: str, body: str = None,
                                 draft: bool = False, owner: str = None) -> Dict[str, Any]:
        """Cria novo pull request"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls"
        
        data = {
            "title": title,
            "head": head,
            "base": base,
            "draft": draft
        }
        if body:
            data["body"] = body
        
        return await self._make_request("POST", endpoint, data)
    
    async def get_pull_request(self, repo: str, pr_number: int,
                               owner: str = None) -> Dict[str, Any]:
        """Obtém detalhes de um PR"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}"
        return await self._make_request("GET", endpoint)
    
    async def merge_pull_request(self, repo: str, pr_number: int,
                                commit_title: str = None,
                                commit_message: str = None,
                                sha: str = None,
                                owner: str = None) -> Dict[str, Any]:
        """Faz merge de um PR"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}/merge"
        
        data = {}
        if commit_title:
            data["commit_title"] = commit_title
        if commit_message:
            data["commit_message"] = commit_message
        if sha:
            data["sha"] = sha
        
        return await self._make_request("PUT", endpoint, data)
    
    async def list_pr_files(self, repo: str, pr_number: int,
                           owner: str = None) -> List[Dict[str, Any]]:
        """Lista arquivos modificados em um PR"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}/files"
        return await self._make_request("GET", endpoint)
    
    # ========== CODE REVIEW ==========
    
    async def create_review(self, repo: str, pr_number: int,
                           body: str = None, event: str = None,
                           comments: List[Dict] = None,
                           owner: str = None) -> Dict[str, Any]:
        """
        Cria review de PR
        
        Args:
            event: APPROVE, REQUEST_CHANGES, COMMENT
        """
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}/reviews"
        
        data = {}
        if body:
            data["body"] = body
        if event:
            data["event"] = event
        if comments:
            data["comments"] = comments
        
        return await self._make_request("POST", endpoint, data)
    
    async def submit_review(self, repo: str, pr_number: int,
                           review_id: int, event: str,
                           body: str = None, owner: str = None) -> Dict[str, Any]:
        """Submete review de PR"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}/reviews/{review_id}/events"
        
        data = {"event": event}
        if body:
            data["body"] = body
        
        return await self._make_request("POST", endpoint, data)
    
    async def list_reviews(self, repo: str, pr_number: int,
                          owner: str = None) -> List[Dict[str, Any]]:
        """Lista reviews de um PR"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/pulls/{pr_number}/reviews"
        return await self._make_request("GET", endpoint)
    
    # ========== COMMITS E BRANCHES ==========
    
    async def list_commits(self, repo: str, owner: str = None,
                          sha: str = None, path: str = None,
                          per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista commits"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/commits"
        
        params = {"per_page": per_page}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def get_commit(self, repo: str, sha: str,
                        owner: str = None) -> Dict[str, Any]:
        """Obtém detalhes de um commit"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/commits/{sha}"
        return await self._make_request("GET", endpoint)
    
    async def list_branches(self, repo: str, owner: str = None,
                           per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista branches"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/branches"
        return await self._make_request("GET", endpoint, params={
            "per_page": per_page
        })
    
    async def create_branch(self, repo: str, branch: str, from_branch: str = "main",
                           owner: str = None) -> Dict[str, Any]:
        """Cria novo branch"""
        target_owner = owner or self.owner
        
        # Primeiro obtém o SHA do branch de origem
        ref_endpoint = f"/repos/{target_owner}/{repo}/git/ref/heads/{from_branch}"
        ref_data = await self._make_request("GET", ref_endpoint)
        sha = ref_data["object"]["sha"]
        
        # Cria novo branch
        endpoint = f"/repos/{target_owner}/{repo}/git/refs"
        return await self._make_request("POST", endpoint, {
            "ref": f"refs/heads/{branch}",
            "sha": sha
        })
    
    # ========== CONTEÚDO ==========
    
    async def get_file_content(self, repo: str, path: str,
                              ref: str = None, owner: str = None) -> Dict[str, Any]:
        """Obtém conteúdo de um arquivo"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/contents/{path}"
        
        params = {}
        if ref:
            params["ref"] = ref
        
        result = await self._make_request("GET", endpoint, params=params)
        
        # Decodifica conteúdo base64
        if "content" in result:
            content = base64.b64decode(result["content"]).decode("utf-8")
            result["decoded_content"] = content
        
        return result
    
    async def create_or_update_file(self, repo: str, path: str,
                                   message: str, content: str,
                                   sha: str = None, branch: str = None,
                                   owner: str = None) -> Dict[str, Any]:
        """Cria ou atualiza arquivo"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/contents/{path}"
        
        # Codifica conteúdo em base64
        encoded_content = base64.b64encode(content.encode()).decode()
        
        data = {
            "message": message,
            "content": encoded_content
        }
        
        if sha:
            data["sha"] = sha  # Necessário para update
        if branch:
            data["branch"] = branch
        
        return await self._make_request("PUT", endpoint, data)
    
    async def delete_file(self, repo: str, path: str,
                         message: str, sha: str,
                         branch: str = None, owner: str = None) -> Dict[str, Any]:
        """Remove arquivo"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/contents/{path}"
        
        data = {
            "message": message,
            "sha": sha
        }
        
        if branch:
            data["branch"] = branch
        
        return await self._make_request("DELETE", endpoint, data)
    
    # ========== ACTIONS / WORKFLOWS ==========
    
    async def list_workflows(self, repo: str, owner: str = None) -> Dict[str, Any]:
        """Lista workflows de CI/CD"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/actions/workflows"
        return await self._make_request("GET", endpoint)
    
    async def list_workflow_runs(self, repo: str, workflow_id: str = None,
                                owner: str = None,
                                per_page: int = 30) -> Dict[str, Any]:
        """Lista execuções de workflows"""
        target_owner = owner or self.owner
        
        if workflow_id:
            endpoint = f"/repos/{target_owner}/{repo}/actions/workflows/{workflow_id}/runs"
        else:
            endpoint = f"/repos/{target_owner}/{repo}/actions/runs"
        
        return await self._make_request("GET", endpoint, params={
            "per_page": per_page
        })
    
    async def trigger_workflow(self, repo: str, workflow_id: str,
                              ref: str, inputs: Dict = None,
                              owner: str = None) -> Dict[str, Any]:
        """Dispara workflow manualmente"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        
        data = {"ref": ref}
        if inputs:
            data["inputs"] = inputs
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== RELEASES ==========
    
    async def list_releases(self, repo: str, owner: str = None,
                           per_page: int = 30) -> List[Dict[str, Any]]:
        """Lista releases"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/releases"
        return await self._make_request("GET", endpoint, params={
            "per_page": per_page
        })
    
    async def create_release(self, repo: str, tag_name: str,
                            name: str = None, body: str = None,
                            draft: bool = False, prerelease: bool = False,
                            target_commitish: str = None,
                            owner: str = None) -> Dict[str, Any]:
        """Cria novo release"""
        target_owner = owner or self.owner
        endpoint = f"/repos/{target_owner}/{repo}/releases"
        
        data = {
            "tag_name": tag_name,
            "draft": draft,
            "prerelease": prerelease
        }
        
        if name:
            data["name"] = name
        if body:
            data["body"] = body
        if target_commitish:
            data["target_commitish"] = target_commitish
        
        return await self._make_request("POST", endpoint, data)
    
    # ========== SEARCH ==========
    
    async def search_code(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        """Busca código"""
        endpoint = "/search/code"
        return await self._make_request("GET", endpoint, params={
            "q": query,
            "per_page": per_page
        })
    
    async def search_issues(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        """Busca issues"""
        endpoint = "/search/issues"
        return await self._make_request("GET", endpoint, params={
            "q": query,
            "per_page": per_page
        })
    
    async def search_repositories(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        """Busca repositórios"""
        endpoint = "/search/repositories"
        return await self._make_request("GET", endpoint, params={
            "q": query,
            "per_page": per_page
        })
    
    # ========== UTILITÁRIOS ==========
    
    async def get_rate_limit(self) -> Dict[str, Any]:
        """Obtém status do rate limit"""
        return await self._make_request("GET", "/rate_limit")
    
    async def get_user(self) -> Dict[str, Any]:
        """Obtém informações do usuário autenticado"""
        return await self._make_request("GET", "/user")
    
    async def test_connection(self) -> bool:
        """Testa conexão"""
        try:
            result = await self.get_rate_limit()
            return "resources" in result
        except:
            return False


# Instância global
github_mcp = None

def init_github_mcp(token: str, owner: str = None):
    """Inicializa o GitHub MCP"""
    global github_mcp
    github_mcp = GitHubMCP(token, owner)
    return github_mcp
