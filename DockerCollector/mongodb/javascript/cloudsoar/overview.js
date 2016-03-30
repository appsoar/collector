overview = function () {
	var data = {};
    data['namespace'] = db.Namespace.find().count();
	data['user'] = db.User.find().count();
	data['repository'] = db.Repository.find().count();

	return {"result":0, "content":data};
}