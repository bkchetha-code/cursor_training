(function () {
  const grid = document.getElementById("metrics-grid");
  if (!grid) return;

  const url = grid.dataset.pollUrl;
  const seconds = Number(grid.dataset.pollSeconds || "8");
  const auto = document.getElementById("auto-refresh");
  const manual = document.getElementById("manual-refresh");
  let timer = null;

  function fmtBytes(n) {
    if (n == null) return "—";
    const u = ["B", "KB", "MB", "GB", "TB"];
    let v = Number(n);
    let i = 0;
    while (v >= 1024 && i < u.length - 1) {
      v /= 1024;
      i += 1;
    }
    return v.toFixed(i === 0 ? 0 : 1) + " " + u[i];
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function render(data) {
    if (!data || !data.ok) {
      const msg = (data && data.error) || "No data yet";
      ["m-cpu", "m-memory", "m-disk", "m-load", "m-network", "m-ports", "m-uptime"].forEach(
        (id) => setText(id, msg)
      );
      const proc = document.getElementById("m-processes");
      if (proc) proc.textContent = msg;
      return;
    }
    const m = data.metrics || {};
    const cpu = m.cpu || {};
    const mem = m.memory || {};
    const disk = (m.disk && m.disk.root) || {};
    const load = m.load || {};
    const net = m.network || {};
    const ports = m.ports || {};
    const up = m.uptime || {};
    const procs = (m.processes && m.processes.top) || [];

    setText("m-cpu", cpu.usage_percent != null ? cpu.usage_percent + "%" : "No data yet");
    setText(
      "m-memory",
      mem.used_bytes != null
        ? fmtBytes(mem.used_bytes) + " / " + fmtBytes(mem.free_bytes) + " (" + mem.used_percent + "%)"
        : "No data yet"
    );
    setText(
      "m-disk",
      disk.used_bytes != null
        ? fmtBytes(disk.used_bytes) + " / " + fmtBytes(disk.free_bytes) + " (" + disk.used_percent + "%)"
        : "No data yet"
    );
    setText(
      "m-load",
      load.load_1 != null ? load.load_1 + " / " + load.load_5 + " / " + load.load_15 : "No data yet"
    );
    setText(
      "m-network",
      net.rx_bytes != null ? "RX " + fmtBytes(net.rx_bytes) + " · TX " + fmtBytes(net.tx_bytes) : "No data yet"
    );
    setText(
      "m-ports",
      ports.tcp != null ? "TCP " + ports.tcp + " · UDP " + ports.udp : "No data yet"
    );
    setText("m-uptime", up.human || "No data yet");

    const procEl = document.getElementById("m-processes");
    if (procEl) {
      if (!procs.length) {
        procEl.textContent = "No data yet";
      } else {
        procEl.innerHTML =
          "<table class='mini-table'><thead><tr><th>PID</th><th>CMD</th><th>CPU</th><th>MEM</th></tr></thead><tbody>" +
          procs
            .map(
              (p) =>
                "<tr><td>" +
                p.pid +
                "</td><td>" +
                p.comm +
                "</td><td>" +
                p.cpu +
                "</td><td>" +
                p.mem +
                "</td></tr>"
            )
            .join("") +
          "</tbody></table>";
      }
    }
  }

  async function refresh() {
    try {
      const res = await fetch(url, { credentials: "same-origin" });
      if (res.status === 401 || res.status === 302) return;
      if (res.status === 429) return;
      const data = await res.json();
      render(data);
    } catch (e) {
      setText("m-cpu", "Refresh failed");
    }
  }

  function schedule() {
    if (timer) clearInterval(timer);
    if (auto && auto.checked) {
      timer = setInterval(refresh, seconds * 1000);
    }
  }

  if (manual) manual.addEventListener("click", refresh);
  if (auto) auto.addEventListener("change", schedule);
  refresh();
  schedule();
})();
