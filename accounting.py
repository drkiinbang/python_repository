# -------------------------
# 실행방법 1
# streamlit run accounting.py
# 실행 방법 2
# cd f:/repository/python_repository
# python -m streamlit run accounting.py
# -------------------------

import plotly.express as px
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime

FILE = "accounting.xlsx"

# 엑셀 파일 로드
def load_excel():
    xls = pd.ExcelFile(FILE)
    return {
        "transactions": pd.read_excel(xls, "transactions"),
        "accounts": pd.read_excel(xls, "accounts"),
        "cards": pd.read_excel(xls, "cards"),
        "categories": pd.read_excel(xls, "categories"),
        "users": pd.read_excel(xls, "users"),
    }

# 엑셀 저장
def save_excel(data):
    with pd.ExcelWriter(FILE, engine="openpyxl") as writer:
        for sheet, df in data.items():
            df.to_excel(writer, sheet_name=sheet, index=False)

# UI 시작
st.title("📊 법인 계좌·카드 관리 시스템")

data = load_excel()

# id 자동 생성 처리
transactions = data["transactions"]
# id 컬럼이 없으면 생성
if "id" not in transactions.columns:
    transactions["id"] = None
# id가 비어 있는 행에 대해 UUID 자동 생성
transactions["id"] = transactions["id"].apply(
    lambda x: str(uuid.uuid4()) if pd.isna(x) or x == "" else x
)
# 다시 저장
data["transactions"] = transactions
save_excel(data)

menu = st.sidebar.selectbox(
    "메뉴 선택",
    [
        "대시보드",
        "입력",
        "월별 통계",
        "연도별 통계",
        "거래 관리",
        "계좌 관리",
        "카드 관리",
        "항목 관리",
        "사용자 관리"
    ]
)

# -------------------------
# 대시보드 페이지
# -------------------------
if menu == "대시보드":
    st.header("📊 대시보드")

    df = data["transactions"]
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # 🔥 연도 선택 추가
    years = sorted(df["year"].unique())
    selected_year = st.selectbox("연도 선택", years)

    # 🔥 선택된 연도 데이터만 사용
    df_year = df[df["year"] == selected_year]

    import plotly.express as px

    # 1) 카드별 지출 파이차트
    st.subheader("💳 카드별 지출 비중")
    card_expense = df_year[df_year["type"] == "지출"].groupby("card")["amount"].sum().reset_index()
    card_expense = card_expense[card_expense["card"] != ""]
    if not card_expense.empty:
        fig = px.pie(card_expense, names="card", values="amount", title=f"{selected_year}년 카드별 지출 비중")
        st.plotly_chart(fig)
    else:
        st.info("지출 데이터가 없습니다.")

    # 2) 계좌별 수입/지출 파이차트
    st.subheader("🏦 계좌별 수입 비중")
    income_acc = df_year[df_year["type"] == "수입"].groupby("account")["amount"].sum().reset_index()
    income_acc = income_acc[income_acc["account"] != ""]
    if not income_acc.empty:
        fig = px.pie(income_acc, names="account", values="amount",
                    title=f"{selected_year}년 계좌별 수입 비중")
        st.plotly_chart(fig)
    else:
        st.info("수입 데이터가 없습니다.")

    st.subheader("🏦 계좌별 지출 비중")
    expense_acc = df_year[df_year["type"] == "지출"].groupby("account")["amount"].sum().reset_index()
    expense_acc = expense_acc[expense_acc["account"] != ""]
    if not expense_acc.empty:
        fig = px.pie(expense_acc, names="account", values="amount",
                    title=f"{selected_year}년 계좌별 지출 비중")
        st.plotly_chart(fig)
    else:
        st.info("지출 데이터가 없습니다.")

    # 3) 월별 지출 추세 라인차트
    st.subheader("📉 월별 지출 추세")
    monthly_expense = df_year[df_year["type"] == "지출"].groupby("month")["amount"].sum().reset_index()
    fig = px.line(monthly_expense, x="month", y="amount", markers=True,
                  title=f"{selected_year}년 월별 지출 추세")
    st.plotly_chart(fig)

    # 4) 월별 수입 추세 라인차트
    st.subheader("📉 월별 수입 추세")
    monthly_expense = df_year[df_year["type"] == "수입"].groupby("month")["amount"].sum().reset_index()
    fig = px.line(monthly_expense, x="month", y="amount", markers=True,
                  title=f"{selected_year}년 월별 수입 추세")
    st.plotly_chart(fig)

    import io

    # 5) 보고서(Excel) 다운로드
    if st.button("📥 Excel 보고서 다운로드"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_year.to_excel(writer, sheet_name="연도별 데이터", index=False)
            card_expense.to_excel(writer, sheet_name="카드별 지출", index=False)
            income_acc.to_excel(writer, sheet_name="계좌별 수입", index=False)
            expense_acc.to_excel(writer, sheet_name="계좌별 지출", index=False)

        st.download_button(
            label="Excel 다운로드",
            data=output.getvalue(),
            file_name=f"report_{selected_year}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# -------------------------
# 입력 페이지
# -------------------------
elif menu == "입력":
    st.header("📥 거래 입력")

    date = st.date_input("날짜")
    type_ = st.selectbox("유형", ["지출", "수입"])
    amount = st.number_input("금액", min_value=0)
    account = st.selectbox("계좌", [""] + list(data["accounts"]["account_name"]))
    card = st.selectbox("카드", [""] + list(data["cards"]["card_name"]))

    # 🔥 유형에 따라 항목 필터링
    filtered_categories = data["categories"][data["categories"]["type"] == type_]
    category = st.selectbox("항목", list(filtered_categories["category_name"]))

    memo = st.text_input("메모")
    created_by = st.selectbox("입력자", list(data["users"]["name"]))

    if st.button("저장"):
        new_row = {
            "id": str(uuid.uuid4()),
            "date": date,
            "type": type_,
            "amount": amount,
            "account": account,
            "card": card,
            "category": category,
            "memo": memo,
            "created_by": created_by,
            "created_at": datetime.now()
        }

        df = data["transactions"]
        df.loc[len(df)] = new_row
        data["transactions"] = df

        save_excel(data)
        st.success("저장 완료!")

# -------------------------
# 월별 통계
# -------------------------
elif menu == "월별 통계":
    st.header("📅 월별 통계")

    df = data["transactions"]
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month

        year = st.selectbox("연도 선택", sorted(df["year"].unique()))
        month = st.selectbox("월 선택", sorted(df[df["year"] == year]["month"].unique()))

        filtered = df[(df["year"] == year) & (df["month"] == month)]

        # -------------------------
        # 🔥 지출 통계
        # -------------------------
        st.subheader("💸 지출 통계")

        expense = filtered[filtered["type"] == "지출"]
        if not expense.empty:
            exp_sum = expense.groupby("category")["amount"].sum().reset_index()
            exp_sum["amount"] = exp_sum["amount"].apply(lambda x: f"{x:,}")
            st.table(exp_sum)

            # 파이차트
            import plotly.express as px
            fig_exp = px.pie(expense.groupby("category")["amount"].sum().reset_index(),
                             names="category", values="amount",
                             title="지출 항목 비중")
            st.plotly_chart(fig_exp)
        else:
            st.info("지출 데이터가 없습니다.")

        # -------------------------
        # 🔥 수입 통계
        # -------------------------
        st.subheader("💰 수입 통계")

        income = filtered[filtered["type"] == "수입"]
        if not income.empty:
            inc_sum = income.groupby("category")["amount"].sum().reset_index()
            inc_sum["amount"] = inc_sum["amount"].apply(lambda x: f"{x:,}")
            st.table(inc_sum)

            fig_inc = px.pie(income.groupby("category")["amount"].sum().reset_index(),
                             names="category", values="amount",
                             title="수입 항목 비중")
            st.plotly_chart(fig_inc)
        else:
            st.info("수입 데이터가 없습니다.")
        
        # -------------------------
        # 🔥 카드별 지출
        # -------------------------
        st.subheader("💳 카드별 지출 비중")
        card_expense = filtered[filtered["type"] == "지출"].groupby("card")["amount"].sum().reset_index()
        card_expense = card_expense[card_expense["card"] != ""]
        if not card_expense.empty:
            fig = px.pie(card_expense, names="card", values="amount", title="카드별 지출 비중")
            st.plotly_chart(fig)
        else:
            st.info("지출 데이터가 없습니다.")

        # -------------------------
        # 🔥 계좌별 수입/지출
        # -------------------------
        st.subheader("🏦 계좌별 수입 비중")
        income_acc = filtered[filtered["type"] == "수입"].groupby("account")["amount"].sum().reset_index()
        income_acc = income_acc[income_acc["account"] != ""]
        if not income_acc.empty:
            fig = px.pie(income_acc, names="account", values="amount",
                        title="계좌별 수입 비중")
            st.plotly_chart(fig)
        else:
            st.info("수입 데이터가 없습니다.")

        st.subheader("🏦 계좌별 지출 비중")
        expense_acc = filtered[filtered["type"] == "지출"].groupby("account")["amount"].sum().reset_index()
        expense_acc = expense_acc[expense_acc["account"] != ""]
        if not expense_acc.empty:
            fig = px.pie(expense_acc, names="account", values="amount",
                        title="계좌별 지출 비중")
            st.plotly_chart(fig)
        else:
            st.info("지출 데이터가 없습니다.")

        # -------------------------
        # 🔥 월별 결산
        # -------------------------
        st.subheader("📘 월별 자동 결산")

        total_income = filtered[filtered["type"] == "수입"]["amount"].sum()
        total_expense = filtered[filtered["type"] == "지출"]["amount"].sum()
        balance = total_income - total_expense

        summary_df = pd.DataFrame({
            "구분": ["총 수입", "총 지출", "계"],
            "금액": [total_income, total_expense, balance]
        })

        summary_df["금액"] = summary_df["금액"].apply(lambda x: f"{x:,}")

        st.table(summary_df)

# -------------------------
# 연도별 통계
# -------------------------
elif menu == "연도별 통계":
    st.header("📆 연도별 통계")

    df = data["transactions"]
    if df.empty:
        st.info("데이터가 없습니다.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        df["year"] = df["date"].dt.year

        year = st.selectbox("연도 선택", sorted(df["year"].unique()))
        filtered = df[df["year"] == year]

        # -------------------------
        # 🔥 지출 통계
        # -------------------------
        st.subheader("💸 지출 통계")

        expense = filtered[filtered["type"] == "지출"]
        if not expense.empty:
            exp_sum = expense.groupby("category")["amount"].sum().reset_index()
            exp_sum["amount"] = exp_sum["amount"].apply(lambda x: f"{x:,}")
            st.table(exp_sum)

            import plotly.express as px
            fig_exp = px.pie(expense.groupby("category")["amount"].sum().reset_index(),
                             names="category", values="amount",
                             title="지출 항목 비중")
            st.plotly_chart(fig_exp)
        else:
            st.info("지출 데이터가 없습니다.")

        # -------------------------
        # 🔥 수입 통계
        # -------------------------
        st.subheader("💰 수입 통계")

        income = filtered[filtered["type"] == "수입"]
        if not income.empty:
            inc_sum = income.groupby("category")["amount"].sum().reset_index()
            inc_sum["amount"] = inc_sum["amount"].apply(lambda x: f"{x:,}")
            st.table(inc_sum)

            fig_inc = px.pie(income.groupby("category")["amount"].sum().reset_index(),
                             names="category", values="amount",
                             title="수입 항목 비중")
            st.plotly_chart(fig_inc)
        else:
            st.info("수입 데이터가 없습니다.")

        # -------------------------
        # 🔥 카드별 지출
        # -------------------------
        st.subheader("💳 카드별 지출 비중")
        card_expense = filtered[filtered["type"] == "지출"].groupby("card")["amount"].sum().reset_index()
        card_expense = card_expense[card_expense["card"] != ""]
        if not card_expense.empty:
            fig = px.pie(card_expense, names="card", values="amount", title="카드별 지출 비중")
            st.plotly_chart(fig)
        else:
            st.info("지출 데이터가 없습니다.")

        # -------------------------
        # 🔥 계좌별 수입/지출
        # -------------------------
        st.subheader("🏦 계좌별 수입 비중")
        income_acc = filtered[filtered["type"] == "수입"].groupby("account")["amount"].sum().reset_index()
        income_acc = income_acc[income_acc["account"] != ""]
        if not income_acc.empty:
            fig = px.pie(income_acc, names="account", values="amount",
                        title="계좌별 수입 비중")
            st.plotly_chart(fig)
        else:
            st.info("수입 데이터가 없습니다.")

        st.subheader("🏦 계좌별 지출 비중")
        expense_acc = filtered[filtered["type"] == "지출"].groupby("account")["amount"].sum().reset_index()
        expense_acc = expense_acc[expense_acc["account"] != ""]
        if not expense_acc.empty:
            fig = px.pie(expense_acc, names="account", values="amount",
                        title="계좌별 지출 비중")
            st.plotly_chart(fig)
        else:
            st.info("지출 데이터가 없습니다.")

# -------------------------
# 거래 관리
# -------------------------
elif menu == "거래 관리":
    st.header("🔍 검색 및 필터")

    df = data["transactions"].copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # -----------------------------
    # 1) 연도 선택
    # -----------------------------
    years = ["전체"] + sorted(df["year"].unique().tolist())
    selected_year = st.selectbox("연도 선택", years)

    if selected_year != "전체":
        df = df[df["year"] == selected_year]

        # -----------------------------
        # 2) 월 선택
        # -----------------------------
        months = ["전체"] + sorted(df["month"].unique().tolist())
        selected_month = st.selectbox("월 선택", months)

        if selected_month != "전체":
            df = df[df["month"] == selected_month]

    # -----------------------------
    # 3) 키워드 검색
    # -----------------------------
    keyword = st.text_input("키워드 검색 (메모)")
    if keyword:
        df = df[df["memo"].str.contains(keyword, na=False)]

    # -----------------------------
    # 4) 거래 목록 표시
    # -----------------------------
    df_display = df.copy()
    df_display["amount"] = df_display["amount"].apply(lambda x: f"{x:,}")

    st.subheader("📄 거래 목록")
    st.dataframe(df_display)

    # -----------------------------
    # 5) 거래 선택
    # -----------------------------
    st.subheader("📝 거래 선택")

    if not df.empty:
        selected_id = st.selectbox("수정 또는 삭제할 거래 선택 (ID)", df["id"])
        selected = df[df["id"] == selected_id].iloc[0]

        st.subheader("✏️ 선택된 거래 수정")

        # 기존 값 불러오기
        date = st.date_input("날짜", selected["date"])
        type_ = st.selectbox("유형", ["지출", "수입"], index=["지출", "수입"].index(selected["type"]))
        amount = st.number_input("금액", min_value=0, value=int(selected["amount"]))

        account_list = [""] + list(data["accounts"]["account_name"])
        account = st.selectbox("계좌", account_list, index=account_list.index(selected["account"]) if selected["account"] in account_list else 0)

        card_list = [""] + list(data["cards"]["card_name"])
        card = st.selectbox("카드", card_list, index=card_list.index(selected["card"]) if selected["card"] in card_list else 0)

        filtered_categories = data["categories"][data["categories"]["type"] == type_]
        category_list = list(filtered_categories["category_name"])
        category = st.selectbox("항목", category_list, index=category_list.index(selected["category"]) if selected["category"] in category_list else 0)

        memo = st.text_input("메모", selected["memo"])
        created_by = st.selectbox("입력자", list(data["users"]["name"]), index=list(data["users"]["name"]).index(selected["created_by"]))

        # -----------------------------
        # 6) 수정 저장
        # -----------------------------
        if st.button("💾 수정 저장"):
            df_all = data["transactions"]
            df_all.loc[df_all["id"] == selected_id, ["date", "type", "amount", "account", "card", "category", "memo", "created_by"]] = [
                date, type_, amount, account, card, category, memo, created_by
            ]
            data["transactions"] = df_all
            save_excel(data)
            st.success("수정 완료!")

        # -----------------------------
        # 7) 삭제
        # -----------------------------
        st.subheader("🗑️ 거래 삭제")
        if st.button("❌ 이 거래 삭제"):
            df_all = data["transactions"]
            df_all = df_all[df_all["id"] != selected_id]
            data["transactions"] = df_all
            save_excel(data)
            st.success("삭제 완료!")

# -------------------------
# 계좌 관리
# -------------------------
elif menu == "계좌 관리":
    st.header("🏦 계좌 관리")

    # 🔥 계좌 잔액 계산
    df = data["transactions"]
    balances = []

    for _, row in data["accounts"].iterrows():
        acc = row["account_name"]
        income = df[(df["account"] == acc) & (df["type"] == "수입")]["amount"].sum()
        expense = df[(df["account"] == acc) & (df["type"] == "지출")]["amount"].sum()
        balance = income - expense
        balances.append(balance)

    accounts_display = data["accounts"].copy()
    accounts_display["잔액"] = balances
    accounts_display["잔액"] = accounts_display["잔액"].apply(lambda x: f"{x:,}")

    st.subheader("계좌 목록 및 잔액")
    st.table(accounts_display)

    st.subheader("계좌 추가")
    name = st.text_input("계좌명")
    bank = st.text_input("은행명")
    number = st.text_input("계좌번호")
    memo = st.text_input("메모")

    if st.button("계좌 추가"):
        df = data["accounts"]
        df.loc[len(df)] = [name, bank, number, memo]
        data["accounts"] = df
        save_excel(data)
        st.success("추가 완료!")

    st.subheader("계좌 삭제")
    delete_target = st.selectbox("삭제할 계좌", list(data["accounts"]["account_name"]))
    if st.button("삭제"):
        df = data["accounts"]
        df = df[df["account_name"] != delete_target]
        data["accounts"] = df
        save_excel(data)
        st.success("삭제 완료!")

# -------------------------
# 카드 관리
# -------------------------
elif menu == "카드 관리":
    st.header("💳 카드 관리")

    st.subheader("카드 목록")
    st.write(data["cards"])

    st.subheader("카드 추가")
    name = st.text_input("카드명")
    issuer = st.text_input("카드사")
    linked = st.selectbox("연결 계좌", list(data["accounts"]["account_name"]))
    memo = st.text_input("메모")

    if st.button("카드 추가"):
        df = data["cards"]
        df.loc[len(df)] = [name, issuer, linked, memo]
        data["cards"] = df
        save_excel(data)
        st.success("추가 완료!")

    st.subheader("카드 삭제")
    delete_target = st.selectbox("삭제할 카드", list(data["cards"]["card_name"]))
    if st.button("삭제"):
        df = data["cards"]
        df = df[df["card_name"] != delete_target]
        data["cards"] = df
        save_excel(data)
        st.success("삭제 완료!")

# -------------------------
# 항목 관리
# -------------------------
elif menu == "항목 관리":
    st.header("📂 항목 관리")

    st.subheader("항목 목록")
    st.write(data["categories"])

    st.subheader("항목 추가")
    name = st.text_input("항목명")
    type_ = st.selectbox("유형", ["지출", "수입"])
    desc = st.text_input("설명")

    if st.button("항목 추가"):
        df = data["categories"]
        df.loc[len(df)] = [name, type_, desc]
        data["categories"] = df
        save_excel(data)
        st.success("추가 완료!")

    st.subheader("항목 삭제")
    delete_target = st.selectbox("삭제할 항목", list(data["categories"]["category_name"]))
    if st.button("삭제"):
        df = data["categories"]
        df = df[df["category_name"] != delete_target]
        data["categories"] = df
        save_excel(data)
        st.success("삭제 완료!")

# -------------------------
# 사용자 관리
# -------------------------
elif menu == "사용자 관리":
    st.header("👤 사용자 관리")

    st.subheader("사용자 목록")
    st.write(data["users"])

    st.subheader("사용자 추가")
    name = st.text_input("이름")
    role = st.text_input("역할")

    if st.button("사용자 추가"):
        df = data["users"]
        df.loc[len(df)] = [str(uuid.uuid4()), name, role]
        data["users"] = df
        save_excel(data)
        st.success("추가 완료!")

    st.subheader("사용자 삭제")
    delete_target = st.selectbox("삭제할 사용자", list(data["users"]["name"]))
    if st.button("삭제"):
        df = data["users"]
        df = df[df["name"] != delete_target]
        data["users"] = df
        save_excel(data)
        st.success("삭제 완료!")

# -------------------------
# 실행 방법은 페이지 상단 참조
# -------------------------