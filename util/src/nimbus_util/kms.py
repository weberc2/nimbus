from nimbus_core import PropertyString, Sub


def key_id_to_key_arn(key_id: PropertyString) -> PropertyString:
    return Sub(
        f"${{arn:aws:kms:${{AWS::Region}}:${{AWS::AccountId}}:key/${{KeyID}}}}",
        KeyID=key_id,
    )

