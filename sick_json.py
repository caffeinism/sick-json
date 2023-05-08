import json
import logging
import re

import pyjson5

re_extra_data_message = re.compile(r"^Extra data .+? near (\d+)$")
re_illegal_character = re.compile(r"^Expected .+? near (\d+), found .+?$")
re_open_brace = re.compile(r"[\[{]")


class JsonNotFound(Exception):
    "Json format not found"


def parse(maybe_json, pydantic_model=None):
    json_objects = []
    while (index := re_open_brace.search(maybe_json)) is not None:
        index = index.span()[0]
        maybe_json = maybe_json[index:]
        try:
            json_objects.append(pyjson5.decode(maybe_json))
            break
        except pyjson5.Json5ExtraData as e:
            logging.debug(
                "There are other strings that are not JSON."
                " Re-explore for the trailing string."
            )
            match = re_extra_data_message.fullmatch(e.message)
            json_objects.append(e.result)
            maybe_json = maybe_json[int(match.group(1)) :]
        except pyjson5.Json5IllegalCharacter as e:
            logging.debug(
                "Invalid string. If True or Flase, correct it."
            )
            match = re_illegal_character.fullmatch(e.message)
            index = int(match.group(1)) - 1
            if maybe_json[index : index + 4] == "True":
                maybe_json = f"{maybe_json[:index]}t{maybe_json[index + 1 :]}"
            elif maybe_json[index : index + 5] == "False":
                maybe_json = f"{maybe_json[:index]}f{maybe_json[index + 1 :]}"
            else:
                maybe_json = maybe_json[index:]
        except Exception as e:
            maybe_json = maybe_json[index+1:]

    if not json_objects:
        raise JsonNotFound

    if pydantic_model is None:
        return sorted(json_objects, key=lambda x: len(json.dumps(x)))[-1]
    else:
        import pydantic

        model = pydantic.main.create_model(
            "Temp",
            __root__=(pydantic_model, ...),
        )
        for json_object in json_objects:
            try:
                return model(__root__=json_object).dict(by_alias=True)["__root__"]
            except pydantic.ValidationError as e:
                logging.debug(f"{json_object} does not conform to the pydantic format.")
        raise JsonNotFound
