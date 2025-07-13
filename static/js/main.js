document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('searchForm');
  const resultArea = document.getElementById('resultArea');
  const toolNameInput = document.getElementById('toolName');
  const bulkValidBtn = document.getElementById('bulkValidBtn');
  const bulkInvalidBtn = document.getElementById('bulkInvalidBtn');

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const toolName = toolNameInput.value.trim();
    if (!toolName) return;
    resultArea.innerHTML = '<div class="text-secondary">検索中...</div>';
    bulkValidBtn.style.display = 'none';
    bulkInvalidBtn.style.display = 'none';
    try {
      const res = await fetch('/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool_name: toolName })
      });
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        renderResults(data);
      } else {
        resultArea.innerHTML = '<div class="text-danger">該当記事がありません。</div>';
      }
    } catch (e) {
      resultArea.innerHTML = '<div class="text-danger">通信エラー: ' + e + '</div>';
    }
  });

  function renderResults(articles) {
    resultArea.innerHTML = '';
    articles.forEach(article => {
      const div = document.createElement('div');
      div.className = 'article-item';
      div.innerHTML = `
        <div class="form-check">
          <input class="form-check-input article-check" type="checkbox" value="" data-url="${article.url}" data-title="${article.title}" data-tool="${article.tool_name}">
          <label class="form-check-label article-title">
            <a href="${article.url}" target="_blank">${article.title}</a>
          </label>
        </div>
        <div class="mt-2">
          <button class="btn btn-success btn-sm me-2 btn-valid">✔有効</button>
          <button class="btn btn-danger btn-sm btn-invalid">✖無効</button>
        </div>
      `;
      // ボタンイベント
      div.querySelector('.btn-valid').onclick = () => validateArticle(article, true, div);
      div.querySelector('.btn-invalid').onclick = () => validateArticle(article, false, div);
      resultArea.appendChild(div);
    });
    // 一括ボタン表示
    bulkValidBtn.style.display = 'inline-block';
    bulkInvalidBtn.style.display = 'inline-block';
  }

  async function validateArticle(article, isValid, div) {
    try {
      const res = await fetch('/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: article.url,
          title: article.title,
          tool_name: article.tool_name,
          is_valid: isValid
        })
      });
      if (res.ok) {
        div.classList.add('disabled');
      } else {
        alert('判定に失敗しました');
      }
    } catch (e) {
      alert('通信エラー: ' + e);
    }
  }

  // 一括有効/無効
  bulkValidBtn.onclick = () => bulkValidate(true);
  bulkInvalidBtn.onclick = () => bulkValidate(false);

  async function bulkValidate(isValid) {
    const checks = document.querySelectorAll('.article-check:checked');
    if (checks.length === 0) return;
    for (const check of checks) {
      const div = check.closest('.article-item');
      const article = {
        url: check.dataset.url,
        title: check.dataset.title,
        tool_name: check.dataset.tool
      };
      await validateArticle(article, isValid, div);
    }
  }
}); 