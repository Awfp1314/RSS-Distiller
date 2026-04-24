import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db_manager import init_db, link_exists, insert_link, _execute

if __name__ == "__main__":
    TEST_LINK = "https://example.com/test-article-opencode"

    print("=" * 50)
    print("db_manager.py 功能验证")
    print("=" * 50)

    print("\n[测试 1] 初始化数据库（建表）...")
    init_db()
    print("  -> 通过 [OK]")

    print("\n[测试 2] 查询不存在的链接...")
    exists = link_exists(TEST_LINK)
    assert not exists, f"预期链接不存在，但查询返回 exists={exists}"
    print(f"  -> link_exists('{TEST_LINK}') = {exists}  [OK]")

    print("\n[测试 3] 插入测试链接...")
    insert_link(TEST_LINK)
    print("  -> 通过 [OK]")

    print("\n[测试 4] 再次查询（应已存在）...")
    exists = link_exists(TEST_LINK)
    assert exists, f"预期链接已存在，但查询返回 exists={exists}"
    print(f"  -> link_exists('{TEST_LINK}') = {exists}  [OK]")

    print("\n[测试 5] 重复插入（验证 INSERT OR IGNORE）...")
    insert_link(TEST_LINK)
    print("  -> 未报错，通过 [OK]")

    print("\n[测试 6] 清理测试数据...")
    _execute(
        "DELETE FROM articles WHERE link = ?",
        [{"type": "text", "value": TEST_LINK}],
    )
    exists_after_delete = link_exists(TEST_LINK)
    assert not exists_after_delete, "清理后链接仍然存在"
    print("  -> 测试数据已清理 [OK]")

    print("\n" + "=" * 50)
    print("全部 6 项测试通过！数据库连通性和读写逻辑已验证。")
    print("=" * 50)
