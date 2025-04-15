from api.v2.schema.RqJobsSchema import MAX_OBJECT_ID_LIST_SIZE


def create_object_id_chunks(object_id_list, chunk_size=MAX_OBJECT_ID_LIST_SIZE):
    object_id_chunks = []
    if len(object_id_list) > 0:
        object_id_chunks = [object_id_list[i:i + chunk_size] for i in range(0, len(object_id_list), chunk_size)]
    return object_id_chunks
