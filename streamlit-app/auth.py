import hmac
import streamlit as st


def require_password(expected: str) -> None:
    """Stops the page until the right password is entered."""
    if st.session_state.get("authenticated"):
        return
    entered = st.text_input("Mot de passe", type="password")
    if entered:
        if hmac.compare_digest(entered, expected):
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Mot de passe incorrect")
    st.stop()