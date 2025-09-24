from commitizen import changelog, cmd
from commitizen.git import GitCommit
from cz_gitmoji.main import CommitizenGitmojiCz


def render_cherry(origin_branch_name: str = "") -> str:
    command = cmd.run(f"git cherry -v {origin_branch_name}")
    if not (commits := command.out.split("\n")[:-1]):
        raise ValueError("不能找到追蹤的遠端分支，請先 push 或手動指定 <上游>。")

    git_commits = [GitCommit(c[1], c[2]) for c in (commit.split(maxsplit=2) for commit in commits)]

    tree = changelog.generate_tree_from_commits(
        git_commits,
        [],
        commit_parser=CommitizenGitmojiCz.commit_parser,
        changelog_pattern=CommitizenGitmojiCz.changelog_pattern,
        change_type_map=CommitizenGitmojiCz.change_type_map,
    )
    order_tree = changelog.generate_ordered_changelog_tree(
        tree, CommitizenGitmojiCz.change_type_order
    )
    return changelog.render_changelog(
        order_tree, CommitizenGitmojiCz.template_loader, "CHANGELOG.md.j2"
    )


if __name__ == "__main__":
    print(render_cherry("origin/dev"))
