import streamlit as st
import yfinance as yf
import requests

# Konfigurace
st.set_page_config(page_title="ContEX", layout="wide")

# ⬅️ SIDEBAR
with st.sidebar:
    st.markdown("### 📁 ContEX")
    ticker = st.text_input("Zadej ticker:", placeholder="např. AAPL, MSFT, TSLA")

    st.markdown("---")
    selected_view = st.sidebar.radio("🧭 Navigace:", [
        "📊 Výsledky akcie",
        "🧰 Nástroje",
        "🔍 Výhled analytiků",
        "📄 10-K report"
    ])

    st.markdown("---")
    st.markdown("🔗 **Externí odkazy:**")
    if ticker:
        st.markdown(f"[Yahoo Finance – {ticker}](https://finance.yahoo.com/quote/{ticker})")
        st.markdown(f"[Finviz – {ticker}](https://finviz.com/quote.ashx?t={ticker})")
        st.markdown(f"[TradingView – {ticker}](https://www.tradingview.com/symbols/{ticker})")
        st.markdown(f"[StockAnalysis – {ticker}](https://stockanalysis.com/stocks/{ticker.lower()})")
                # AlphaSpread – potřebuje burzu v URL; zkusíme ji zjistit a namapovat
        try:
            ex_raw = yf.Ticker(ticker).info.get("exchange", "")
            ex_map = {
                "NMS": "nasdaq", "NASDAQ": "nasdaq",
                "NYQ": "nyse",   "NYSE": "nyse",
                "ASE": "amex",   "AMEX": "amex"
            }
            ex_slug = ex_map.get(str(ex_raw).upper(), "nasdaq")
        except Exception:
            ex_slug = "nasdaq"

        st.markdown(f"[AlphaSpread – {ticker}](https://www.alphaspread.com/security/{ex_slug}/{ticker.lower()}/valuation)")
        st.markdown(f"[OptionCharts.io – {ticker}](https://optioncharts.io/stocks/{ticker.upper()})")
        st.markdown("[ChatGPT](https://chat.openai.com) ☁️")
# 📋 HLAVNÍ OBSAH
if selected_view == "📊 Výsledky akcie":
    st.title("📊 Výsledky")
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            st.subheader(f"📄 Základní data pro: {info.get('longName', ticker)}")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Aktuální cena:** ${info.get('currentPrice', 'N/A')}")
                st.write(f"**P/E poměr:** {info.get('trailingPE', 'N/A')}")
                st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
                st.write(f"**EPS (TTM):** {info.get('trailingEps', 'N/A')}")

            with col2:
                def format_miliony(value):
                    if value is None:
                        return "N/A"
                    try:
                        value = float(value)
                        if value >= 1_000_000_000_000:
                            return f"${value / 1_000_000_000_000:.2f} bilionů"
                        elif value >= 1_000_000_000:
                            return f"${value / 1_000_000_000:.2f} miliard"
                        elif value >= 1_000_000:
                            return f"${value / 1_000_000:.2f} milionů"
                        else:
                            return f"${value:,.0f}"
                    except:
                        return "N/A"

                st.write(f"**Dluh (totalDebt):** {format_miliony(info.get('totalDebt'))}")
                st.write(f"**Hotovost (totalCash):** {format_miliony(info.get('totalCash'))}")

            # Dluhová zátěž
            debt = info.get("totalDebt", None)
            ebitda = info.get("ebitda", None)

            st.markdown("#### 🧾 Dluhová zátěž")

            if debt and ebitda and ebitda != 0:
                debt_ebitda = round(debt / ebitda, 2)

                if debt_ebitda <= 2.5:
                    st.success(f"Dluh / EBITDA: {debt_ebitda} ✅ (nízká zadluženost)")
                elif debt_ebitda <= 4:
                    st.warning(f"Dluh / EBITDA: {debt_ebitda} ⚠️ (střední zadluženost)")
                else:
                    st.error(f"Dluh / EBITDA: {debt_ebitda} ❗ (vysoká zadluženost)")
            else:
                st.write("Dluh / EBITDA: N/A")

            st.write(f"Debt / Equity: {info.get('debtToEquity', 'N/A')}")

        except Exception as e:
            st.error(f"Nastala chyba při načítání dat: {e}")
    else:
        st.info("Zadej výše ticker akcie.")

elif selected_view == "🧰 Nástroje":
    st.title("🧰 Nástroje")

    # 📈 CAGR kalkulačka
    with st.expander("📈 Kalkulačka CAGR"):
        start = st.number_input("Počáteční hodnota", min_value=0.0, value=100.0, key="cagr_start")
        end = st.number_input("Konečná hodnota", min_value=0.0, value=200.0, key="cagr_end")
        years = st.number_input("Počet let", min_value=1.0, value=5.0, key="cagr_years")

        if start > 0 and years > 0:
            cagr = ((end / start) ** (1 / years)) - 1
            st.success(f"CAGR: {cagr*100:.2f} %")

    # 🧮 PEG kalkulačka
    with st.expander("🧮 Výpočet PEG poměru"):
        pe = st.number_input("P/E poměr", min_value=0.0, value=20.0, key="peg_pe")
        growth = st.number_input("Očekávaný roční růst EPS (%)", min_value=0.1, value=15.0, key="peg_growth")

        if growth > 0:
            peg = pe / growth
            st.success(f"PEG poměr: {peg:.2f}")
        else:
            st.warning("Růst nesmí být nulový.")

    # 🔮 Buffettův model + Margin of Safety
    with st.expander("🔮 Výpočet vnitřní hodnoty (Buffettův model)"):
        eps = st.number_input("Aktuální EPS", min_value=0.0, value=5.0, step=0.1, key="buffett_eps")
        rust_eps = st.number_input("Odhad ročního růstu EPS (%)", min_value=0.0, value=12.0, step=0.1, key="buffett_growth")
        aktualni_cena = st.number_input("Aktuální tržní cena akcie", min_value=0.0, value=100.0, step=1.0, key="buffett_price")

        vnitrni_hodnota = eps * (7 + 1.5 * rust_eps)
        st.success(f"Vnitřní hodnota akcie: ${vnitrni_hodnota:.2f}")

        if vnitrni_hodnota > 0:
            mos = (vnitrni_hodnota - aktualni_cena) / vnitrni_hodnota * 100
            if mos >= 30:
                st.success(f"✅ Margin of Safety: {mos:.1f} % – výborná rezerva!")
            elif mos >= 15:
                st.info(f"🟡 Margin of Safety: {mos:.1f} % – přijatelná rezerva")
            elif mos >= 0:
                st.warning(f"🟠 Margin of Safety: {mos:.1f} % – malá rezerva")
            else:
                st.error(f"🔴 Akcie je dražší než vnitřní hodnota ({mos:.1f} %)")
        else:
            st.warning("Vnitřní hodnota je 0 – nelze spočítat Margin of Safety.")
    # 📏 Výnos z tržeb / zisku (vs. Market Cap)
    with st.expander("📏 Výnos z tržeb / zisku vůči Market Cap"):
        # Načtení defaultů z Yahoo (pokud je vyplněný ticker)
        default_rev = default_profit = default_mcap = 0.0
        if ticker:
            try:
                _t = yf.Ticker(ticker)
                _info = _t.info or {}
                default_rev = float(_info.get("totalRevenue") or 0.0)
                # netIncomeToCommon bývá dostupnější; fallback na netIncome
                default_profit = float(_info.get("netIncomeToCommon") or _info.get("netIncome") or 0.0)
                default_mcap = float(_info.get("marketCap") or 0.0)
            except Exception:
                pass

        use_yahoo = st.checkbox("Načíst hodnoty z Yahoo Finance", value=bool(ticker))

        rev = st.number_input("Tržby (Total Revenue, $)", min_value=0.0,
                              value=(default_rev if use_yahoo else 0.0), step=1_000_000.0, format="%.0f")
        profit = st.number_input("Čistý zisk (Net Income, $)", min_value=0.0,
                                 value=(default_profit if use_yahoo else 0.0), step=1_000_000.0, format="%.0f")
        mcap = st.number_input("Tržní kapitalizace (Market Cap, $)", min_value=0.0,
                               value=(default_mcap if use_yahoo else 0.0), step=1_000_000.0, format="%.0f")

        st.markdown("---")
        if mcap > 0:
            rev_yield = rev / mcap * 100.0 if rev > 0 else 0.0
            earn_yield = profit / mcap * 100.0 if profit > 0 else 0.0

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Výnos z tržeb", f"{rev_yield:.2f} %")
                if rev_yield > 0:
                    ps = 100.0 / rev_yield
                    st.write(f"P/S ≈ **{ps:.2f}**")
            with col2:
                st.metric("Výnos ze zisku", f"{earn_yield:.2f} %")
                if earn_yield > 0:
                    pe = 100.0 / earn_yield
                    st.write(f"P/E ≈ **{pe:.2f}**")
        else:
            st.info("Zadej kladnou tržní kapitalizaci pro výpočet.")

elif selected_view == "🔍 Výhled analytiků":
    st.title("🔍 Výhled analytiků")
    
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            st.markdown(f"### Analytický pohled pro: **{info.get('longName', ticker)}**")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Průměrný odhad ceny:** ${info.get('targetMeanPrice', 'N/A')}")
                st.write(f"**Nejvyšší cílová cena:** ${info.get('targetHighPrice', 'N/A')}")
                st.write(f"**Nejnižší cílová cena:** ${info.get('targetLowPrice', 'N/A')}")

            with col2:
                st.write(f"**Počet analytiků:** {info.get('numberOfAnalystOpinions', 'N/A')}")
                st.write(f"**Doporučení:** {info.get('recommendationKey', 'N/A').capitalize()}")

            st.markdown("---")
            st.markdown("📌 Poznámka: Tato data pochází z Yahoo Finance. Mohou se lišit podle dostupnosti.")

        except Exception as e:
            st.error(f"Nastala chyba při načítání dat: {e}")
    else:
        st.info("Zadej ticker akcie vlevo v panelu.")

elif selected_view == "📄 10-K report":
    st.title("📄 Vyhledání 10-K reportu")

    if ticker:
        st.info(f"Vyhledávám poslední 10-K report pro: `{ticker.upper()}`")

        sec_search_url = f"https://www.sec.gov/edgar/search/#/q={ticker}%2010-K&category=custom&startdt=2023-01-01&enddt=2025-12-31"

        st.markdown("---")
        st.markdown(f"🔗 [Otevřít výsledky na SEC.gov (v novém okně)]({sec_search_url})")

        st.markdown("""
            - Po otevření můžeš kliknout na nejnovější záznam typu **10-K**
            - Následně klikni na **„Documents“** a otevři soubor s příponou `.htm` nebo `.html`
            - Ten budeš moci přeložit v prohlížeči (např. Chrome → klikni pravým → *„Přeložit do češtiny“*)
        """)
    else:
        st.warning("Zadej vlevo v panelu ticker akcie, např. AAPL nebo MSFT.")

# 📓 POZNÁMKY – ZOBRAZENÍ V HLAVNÍM PANELU
if "show_notes" not in st.session_state:
    st.session_state.show_notes = False
if "user_notes" not in st.session_state:
    st.session_state.user_notes = ""

st.sidebar.markdown("---")
if st.sidebar.button("🟩 Poznámky (otevřít/zavřít)"):
    st.session_state.show_notes = not st.session_state.show_notes

if st.session_state.show_notes:
    st.markdown("### 🗒️ Moje poznámky")
    st.session_state.user_notes = st.text_area(
        "Zapiš si poznámky k akcii, výpočtu nebo myšlenky:",
        st.session_state.user_notes,
        height=200
    )
