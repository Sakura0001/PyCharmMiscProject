const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const dir = path.resolve('artifacts/generated_sql');
const files = fs.readdirSync(dir)
  .filter((file) => /^bp_s04_.*readahead.*\.sql$/.test(file))
  .sort();

const summaryPath = path.join(dir, 'readahead_async_read_summary.tsv');
const progressPath = path.join(dir, 'readahead_run_progress.log');

function ts() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, '');
}

function parseRows(stdout) {
  const rows = [];
  let header = null;
  for (const line of stdout.split(/\r?\n/)) {
    if (!line.trim()) continue;
    const cols = line.split('\t');
    if (cols.includes('check_point') && cols.includes('async_read_pages') && cols.includes('async_read_bytes')) {
      header = cols;
      continue;
    }
    if (header && cols[0] && /_check$/.test(cols[0])) {
      rows.push(Object.fromEntries(header.map((name, index) => [name, cols[index] ?? ''])));
      header = null;
    }
  }
  return rows;
}

function updateDescription(file, rows) {
  const full = path.join(dir, file);
  let sql = fs.readFileSync(full, 'utf8');
  const result = rows.length
    ? `读结果：${rows.map((row) => `${row.check_point} async_pages=${row.async_read_pages} async_bytes=${row.async_read_bytes} sync_pages=${row.sync_read_pages || ''} sync_bytes=${row.sync_read_bytes || ''}`).join('; ')}。`
    : '异步读结果：未获取。';
  sql = sql.replace(/^(-- description\s+:\s*)(.*)$/m, (_match, prefix, desc) => {
    const clean = desc.replace(/\s*(?:异步读结果|读结果)：.*$/, '').trim();
    return `${prefix}${clean} ${result}`;
  });
  fs.writeFileSync(full, sql);
}

fs.writeFileSync(progressPath, '');
fs.writeFileSync(summaryPath, 'file\texit_code\tstatus\tcheck_point\tasync_read_pages\tasync_read_bytes\tsync_read_pages\tsync_read_bytes\ttarget_object_storage_bytes\toutput_txt\n');

for (let index = 0; index < files.length; index += 1) {
  const file = files[index];
  const sqlPath = path.join(dir, file);
  const outPath = path.join(dir, file.replace(/\.sql$/, '.output.txt'));
  const start = `${ts()} START ${index + 1}/${files.length} ${file}`;
  fs.appendFileSync(progressPath, `${start}\n`);
  console.log(start);

  const result = cp.spawnSync('mysql', ['-uroot', '--batch', '--raw', '--force', '--show-warnings', 'test'], {
    input: fs.readFileSync(sqlPath, 'utf8'),
    encoding: 'utf8',
    maxBuffer: 1024 * 1024 * 80,
    env: { ...process.env, MYSQL_PWD: 'Taurus_123' },
  });
  const combined = `${result.stderr || ''}${result.stdout || ''}`;
  fs.writeFileSync(outPath, combined);

  const rows = parseRows(result.stdout || '');
  const status = result.status === 0 && rows.length > 0 ? 'OK' : 'FAIL';
  updateDescription(file, rows);
  if (rows.length) {
    for (const row of rows) {
      fs.appendFileSync(summaryPath, [
        file,
        String(result.status ?? ''),
        status,
        row.check_point || '',
        row.async_read_pages || '',
        row.async_read_bytes || '',
        row.sync_read_pages || '',
        row.sync_read_bytes || '',
        row.target_object_storage_bytes || '',
        outPath,
      ].join('\t') + '\n');
    }
  } else {
    fs.appendFileSync(summaryPath, [file, String(result.status ?? ''), status, '', '', '', '', '', '', outPath].join('\t') + '\n');
  }

  const end = `${ts()} END ${index + 1}/${files.length} ${file} exit=${result.status ?? ''} rows=${rows.length} status=${status}`;
  fs.appendFileSync(progressPath, `${end}\n`);
  console.log(end);
}
