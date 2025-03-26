@dp.callback_query(lambda c: c.data in [plan[1] for plan in get_base_plan()])
    id_plan = selected_plan[-1]
    name_plan = get_plan_name_by_id(id_plan)
    user_id = callback_query.from_user.id
    update_user_current_plan(user_id,name_plan)
    await bot.send_message(callback_query.from_user.id, f"Вы выбрали план: {selected_plan}.")
    # Здесь можно добавить логику для обработки выбранного плана