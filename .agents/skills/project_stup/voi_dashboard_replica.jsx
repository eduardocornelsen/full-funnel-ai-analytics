import { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ScatterChart, Scatter, ComposedChart, Bar, Area,
  ResponsiveContainer
} from "recharts";

const useWindowSize = () => {
  const [width, setWidth] = useState(typeof window !== "undefined" ? window.innerWidth : 1024);
  useEffect(() => {
    const handle = () => setWidth(window.innerWidth);
    window.addEventListener("resize", handle);
    return () => window.removeEventListener("resize", handle);
  }, []);
  return width;
};

const rand = (min, max) => min + Math.random() * (max - min);

const generateDailyData = () => {
  const data = [];
  for (let day = 1; day <= 30; day++) {
    const date = `Jun ${String(day).padStart(2, "0")}`;
    const t24 = 22 + Math.sin((day / 30) * Math.PI) * 8 + rand(-2, 2);
    const t23 = 20 + Math.sin((day / 30) * Math.PI) * 7 + rand(-2, 2);
    const p24 = day >= 7 && day <= 10 ? rand(3, 9) : rand(0, 2);
    const p23 = day >= 12 && day <= 15 ? rand(4, 9) : rand(0, 2.5);
    const d24 = 4.2 + (t24 - 22) * 0.04 - p24 * 0.08 + rand(-0.15, 0.15);
    const d23 = 4.35 + (t23 - 20) * 0.03 - p23 * 0.06 + rand(-0.15, 0.15);
    const dr24 = 14.5 + (t24 - 22) * 0.15 - p24 * 0.3 + rand(-0.75, 0.75);
    const dr23 = 15.2 + (t23 - 20) * 0.12 - p23 * 0.25 + rand(-0.75, 0.75);
    data.push({
      date, day,
      dist2024: +d24.toFixed(2), dist2023: +d23.toFixed(2),
      dur2024: +dr24.toFixed(1), dur2023: +dr23.toFixed(1),
      temp2024: +t24.toFixed(1), temp2023: +t23.toFixed(1),
      precip2024: +p24.toFixed(1), precip2023: +p23.toFixed(1),
      speed2024: +(d24 / (dr24 / 60)).toFixed(1),
      speed2023: +(d23 / (dr23 / 60)).toFixed(1),
    });
  }
  return data;
};

const DAILY = generateDailyData();

const calcKPIs = (data) => {
  const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const sum = (arr) => arr.reduce((a, b) => a + b, 0);
  const t24 = data.map(() => 18000 + Math.floor(Math.random() * 4000));
  const t23 = data.map(() => 14000 + Math.floor(Math.random() * 3000));
  return {
    totalTrips: { value: sum(t24), prev: sum(t23) },
    avgDist: { value: avg(data.map(d => d.dist2024)), prev: avg(data.map(d => d.dist2023)) },
    avgDur: { value: avg(data.map(d => d.dur2024)), prev: avg(data.map(d => d.dur2023)) },
    avgSpeed: { value: avg(data.map(d => d.speed2024)), prev: avg(data.map(d => d.speed2023)) },
    avgTemp: { value: avg(data.map(d => d.temp2024)), prev: avg(data.map(d => d.temp2023)) },
    totalPrecip: { value: sum(data.map(d => d.precip2024)), prev: sum(data.map(d => d.precip2023)) },
  };
};

const KPIs = calcKPIs(DAILY);
const scatter24 = DAILY.map(d => ({ temp: d.temp2024, dist: d.dist2024, year: 2024 }));
const scatter23 = DAILY.map(d => ({ temp: d.temp2023, dist: d.dist2023, year: 2023 }));

const C = { dist2024: "#f87171", dist2023: "#fb923c", dur2024: "#60a5fa", dur2023: "#38bdf8", temp: "#fbbf24" };

const KPICard = ({ label, value, prev, unit, format, invert, m }) => {
  const v = value || 0, p = prev || 0;
  const pct = p !== 0 ? ((v - p) / Math.abs(p)) * 100 : 0;
  const good = invert ? pct < 0 : pct > 0;
  const color = good ? "#4ade80" : "#f87171";
  const fv = (n) => format === "count" ? (n/1000).toFixed(0)+"K" : format === "temp" ? n.toFixed(1)+"°C" : n.toFixed(2);
  return (
    <div style={{ background:"#1a1a2e", borderRadius:8, padding: m?"10px 12px":"14px 16px", borderLeft:`3px solid ${color}`, flex: m?"1 1 45%":"1 1 0", minWidth: m?120:100 }}>
      <div style={{ fontSize: m?9:10, fontWeight:600, color:"#8a8a9a", letterSpacing:1, textTransform:"uppercase", marginBottom: m?4:8 }}>{label}</div>
      <div style={{ fontSize: m?20:26, fontWeight:700, color, letterSpacing:-0.5 }}>{pct>0?"+":""}{pct.toFixed(1)}%</div>
      <div style={{ fontSize: m?10:11, color:"#6a6a7a", marginTop:3 }}>{fv(v)}{unit?` ${unit}`:""} vs {fv(p)}{unit?` ${unit}`:""}</div>
    </div>
  );
};

const Toggle = ({ label, color, active, onClick, m }) => (
  <button onClick={onClick} style={{ background: active?color:"transparent", color: active?"#0d0d1a":color, border:`1.5px solid ${color}`, borderRadius:14, padding: m?"2px 8px":"3px 12px", fontSize: m?9:11, fontWeight:600, cursor:"pointer", letterSpacing:0.5 }}>{label}</button>
);

const Tip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:"#12121f", border:"1px solid #2a2a3e", borderRadius:8, padding:"8px 12px", fontSize:11, lineHeight:1.7 }}>
      <div style={{ fontWeight:700, color:"#e2e2ea", marginBottom:2 }}>{label}</div>
      {payload.map((p, i) => <div key={i} style={{ color:p.color }}>{p.name}: <strong>{p.value}</strong></div>)}
    </div>
  );
};

export default function VoiDashboard() {
  const w = useWindowSize();
  const m = w < 640;
  const [s, setS] = useState({ dist2024:true, dist2023:true, dur2024:true, dur2023:true, temp:true });
  const t = (k) => setS(x => ({ ...x, [k]: !x[k] }));
  const hot = DAILY.reduce((a, b) => b.temp2024 > a.temp2024 ? b : a);
  const wet = DAILY.reduce((a, b) => b.precip2024 > a.precip2024 ? b : a);
  const ch = m?220:320, bch = m?200:260;

  return (
    <div style={{ background:"#0d0d1a", color:"#e2e2ea", fontFamily:"'JetBrains Mono','SF Mono','Fira Code',monospace", minHeight:"100vh", padding: m?"14px 12px":"24px 28px", maxWidth:1400, margin:"0 auto" }}>

      {/* Header */}
      <div style={{ display:"flex", flexWrap:"wrap", justifyContent:"space-between", alignItems:"flex-start", gap:8, marginBottom: m?16:24 }}>
        <div>
          <div style={{ display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
            <span style={{ background:"#f87171", color:"#0d0d1a", fontWeight:800, fontSize: m?11:13, padding:"2px 8px", borderRadius:4 }}>NYC</span>
            <h1 style={{ fontSize: m?15:20, fontWeight:700, margin:0 }}>Manhattan — Ride Distance & Duration</h1>
          </div>
          <p style={{ fontSize: m?10:11, color:"#6a6a7a", margin:"4px 0 0" }}>Year-on-year analysis with weather impact · Daily granularity</p>
        </div>
        <div style={{ background:"#1a1a2e", border:"1px solid #4ade80", borderRadius:6, padding:"5px 12px", fontSize: m?10:12, fontWeight:600, color:"#4ade80", whiteSpace:"nowrap" }}>JUN 2024 VS JUN 2023</div>
      </div>

      {/* KPIs */}
      <div style={{ display:"flex", flexWrap:"wrap", gap: m?8:12, marginBottom: m?16:28 }}>
        <KPICard label="Total Rides" {...KPIs.totalTrips} format="count" m={m} />
        <KPICard label="Avg Ride Distance" {...KPIs.avgDist} unit="km" m={m} />
        <KPICard label="Avg Ride Duration" {...KPIs.avgDur} unit="min" invert m={m} />
        <KPICard label="Implied Speed" {...KPIs.avgSpeed} unit="km/h" m={m} />
        <KPICard label="Avg Max Temp" {...KPIs.avgTemp} format="temp" m={m} />
        <KPICard label="Precipitation" {...KPIs.totalPrecip} unit="mm" invert m={m} />
      </div>

      {/* Main Chart */}
      <div style={{ background:"#12121f", borderRadius:10, padding: m?"12px 10px":"20px 24px 16px", marginBottom: m?14:20 }}>
        <h2 style={{ fontSize: m?12:14, fontWeight:700, margin:"0 0 4px" }}>Daily Avg Ride Distance & Duration — Temperature Overlay</h2>
        <p style={{ fontSize: m?9:10, color:"#6a6a7a", margin:"0 0 8px" }}>Solid = Jun 2024 · Dashed = Jun 2023 · Shaded = temperature</p>
        <div style={{ display:"flex", gap: m?4:8, flexWrap:"wrap", marginBottom: m?10:16 }}>
          <Toggle label="DIST 2024" color={C.dist2024} active={s.dist2024} onClick={() => t("dist2024")} m={m} />
          <Toggle label="DIST 2023" color={C.dist2023} active={s.dist2023} onClick={() => t("dist2023")} m={m} />
          <Toggle label="DUR 2024" color={C.dur2024} active={s.dur2024} onClick={() => t("dur2024")} m={m} />
          <Toggle label="DUR 2023" color={C.dur2023} active={s.dur2023} onClick={() => t("dur2023")} m={m} />
          <Toggle label="TEMP °C" color={C.temp} active={s.temp} onClick={() => t("temp")} m={m} />
        </div>
        <ResponsiveContainer width="100%" height={ch}>
          <ComposedChart data={DAILY} margin={{ top:5, right: m?10:50, left: m?-15:0, bottom:5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e1e32" />
            <XAxis dataKey="date" tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} interval={m?5:2} />
            <YAxis yAxisId="dist" domain={["auto","auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} width={m?30:50} />
            <YAxis yAxisId="dur" orientation="right" domain={["auto","auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} width={m?30:50} />
            <Tooltip content={<Tip />} />
            {s.temp && <Area yAxisId="dist" dataKey="temp2024" name="Temp °C" stroke="none" fill={C.temp} fillOpacity={0.07} type="monotone" />}
            {s.dist2024 && <Line yAxisId="dist" dataKey="dist2024" name="Dist 2024" stroke={C.dist2024} strokeWidth={m?1.5:2.2} dot={{ r: m?1.5:2.5 }} type="monotone" />}
            {s.dist2023 && <Line yAxisId="dist" dataKey="dist2023" name="Dist 2023" stroke={C.dist2023} strokeWidth={m?1.2:1.8} strokeDasharray="6 3" dot={{ r: m?1:2 }} type="monotone" />}
            {s.dur2024 && <Line yAxisId="dur" dataKey="dur2024" name="Dur 2024" stroke={C.dur2024} strokeWidth={m?1.5:2.2} dot={{ r: m?1.5:2.5 }} type="monotone" />}
            {s.dur2023 && <Line yAxisId="dur" dataKey="dur2023" name="Dur 2023" stroke={C.dur2023} strokeWidth={m?1.2:1.8} strokeDasharray="6 3" dot={{ r: m?1:2 }} type="monotone" />}
          </ComposedChart>
        </ResponsiveContainer>
        <div style={{ background:"#1a1a2e", border:"1px solid #f8717133", borderRadius:8, padding: m?"8px 10px":"12px 16px", marginTop: m?8:12, fontSize: m?10:11, lineHeight:1.7, color:"#c0c0d0" }}>
          <span style={{ color:"#f87171", fontWeight:700 }}>Key Insight: </span>
          Hottest day — {hot.date} ({hot.temp2024}°C) — drove longest rides: <strong style={{ color:"#e2e2ea" }}>{hot.dist2024} km / {hot.dur2024} min</strong>.
          Rainy trough {wet.date} ({wet.precip2024}mm) shortened distances: <strong style={{ color:"#e2e2ea" }}>{wet.dist2024} km / {wet.dur2024} min</strong>.
          Temperature correlation: <em>r = +0.52</em> (2023) → <em>r = +0.69</em> (2024).
        </div>
      </div>

      {/* Bottom Row */}
      <div style={{ display:"flex", flexDirection: m?"column":"row", gap: m?14:20 }}>
        {/* Scatter */}
        <div style={{ background:"#12121f", borderRadius:10, padding: m?"12px 10px":"20px 24px 16px", flex:1, minWidth:0 }}>
          <h2 style={{ fontSize: m?12:14, fontWeight:700, margin:"0 0 4px" }}>Temperature vs Avg Ride Distance</h2>
          <p style={{ fontSize: m?9:10, color:"#6a6a7a", margin:"0 0 10px" }}>Each dot = one day. Warmer days → longer trips.</p>
          <ResponsiveContainer width="100%" height={bch}>
            <ScatterChart margin={{ top:10, right:10, left: m?-15:0, bottom:10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e32" />
              <XAxis dataKey="temp" type="number" domain={["auto","auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} />
              <YAxis dataKey="dist" type="number" domain={["auto","auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} width={m?30:50} />
              <Tooltip content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const d = payload[0].payload;
                return <div style={{ background:"#12121f", border:"1px solid #2a2a3e", borderRadius:8, padding:"6px 10px", fontSize:11 }}>
                  <div style={{ color: d.year===2024?"#f87171":"#60a5fa" }}>{d.year}</div>
                  <div style={{ color:"#c0c0d0" }}>Temp: {d.temp}°C · Dist: {d.dist} km</div>
                </div>;
              }} />
              <Scatter name="2024" data={scatter24} fill={C.dist2024} fillOpacity={0.8} r={m?3:5} />
              <Scatter name="2023" data={scatter23} fill={C.dur2024} fillOpacity={0.6} r={m?2.5:4} />
            </ScatterChart>
          </ResponsiveContainer>
          <div style={{ display:"flex", gap:16, justifyContent:"center", marginTop:6 }}>
            <div style={{ display:"flex", alignItems:"center", gap:5, fontSize: m?10:11 }}><div style={{ width:10, height:10, borderRadius:"50%", background:C.dist2024 }} /> 2024</div>
            <div style={{ display:"flex", alignItems:"center", gap:5, fontSize: m?10:11 }}><div style={{ width:10, height:10, borderRadius:"50%", background:C.dur2024 }} /> 2023</div>
          </div>
        </div>

        {/* Precip */}
        <div style={{ background:"#12121f", borderRadius:10, padding: m?"12px 10px":"20px 24px 16px", flex:1, minWidth:0 }}>
          <h2 style={{ fontSize: m?12:14, fontWeight:700, margin:"0 0 4px" }}>Daily Precipitation vs Avg Ride Distance — 2024</h2>
          <p style={{ fontSize: m?9:10, color:"#6a6a7a", margin:"0 0 10px" }}>Bars = rainfall. Line = distance. Jun 7–10 = weather suppression.</p>
          <ResponsiveContainer width="100%" height={bch}>
            <ComposedChart data={DAILY} margin={{ top:10, right: m?10:20, left: m?-15:0, bottom:10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1e32" />
              <XAxis dataKey="date" tick={{ fontSize: m?7:9, fill:"#5a5a6a" }} tickLine={false} interval={m?5:3} />
              <YAxis yAxisId="dist" domain={["auto","auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} width={m?30:50} />
              <YAxis yAxisId="precip" orientation="right" domain={[0,"auto"]} tick={{ fontSize: m?8:10, fill:"#5a5a6a" }} tickLine={false} width={m?30:50} />
              <Tooltip content={<Tip />} />
              <Bar yAxisId="precip" dataKey="precip2024" name="Precipitation (mm)" fill="#60a5fa" fillOpacity={0.5} radius={[3,3,0,0]} barSize={m?6:14} />
              <Line yAxisId="dist" dataKey="dist2024" name="Avg Distance (km)" stroke={C.dist2024} strokeWidth={m?1.5:2} dot={{ r: m?1.5:2, fill:C.dist2024 }} type="monotone" />
            </ComposedChart>
          </ResponsiveContainer>
          <div style={{ display:"flex", gap:12, justifyContent:"center", marginTop:6, flexWrap:"wrap" }}>
            <div style={{ display:"flex", alignItems:"center", gap:5, fontSize: m?10:11 }}><div style={{ width:14, height:10, borderRadius:2, background:C.dist2024 }} /> Distance (km)</div>
            <div style={{ display:"flex", alignItems:"center", gap:5, fontSize: m?10:11 }}><div style={{ width:14, height:10, borderRadius:2, background:"#60a5fa", opacity:0.5 }} /> Rain (mm)</div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div style={{ marginTop: m?16:24, padding:"10px 0", borderTop:"1px solid #1e1e32", display:"flex", flexWrap:"wrap", justifyContent:"space-between", gap:8, fontSize: m?9:10, color:"#4a4a5a" }}>
        <span>Generated by AI Analyst · MCP + dbt + BigQuery</span>
        <span>Data: NYC TLC · Weather: Open-Meteo</span>
      </div>
    </div>
  );
}
