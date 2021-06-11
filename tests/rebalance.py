def trade_calc(old_token1, old_token2, _value):
    fees = 3 * _value // 1000
    _value -= fees

    new_token1 = old_token1 + _value
    new_token2 = old_token1 * old_token2 // new_token1
    send_amt = old_token2 - new_token2
    return send_amt

print(trade_calc(571428571428571428571428, 955636925545322456559995, 1000))
