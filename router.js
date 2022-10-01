const express = require('express')
const Paper = require('./mongoose')

//创建路由容器
let router = express.Router()

router.get('/api/paper', async function (req, res) {
  let data = await Paper.find({}, { date: 1 })
  res.send(data)
})
router.get('/api/paper/classify', async function (req, res) {
  let params = req.query.classify
  data = await Paper.aggregate([
    { $unwind: `$${params}` },
    {
      $group: {
        _id: `$${params}`,
        value: { $sum: 1 }
      }
    }
  ])
  res.send(data)
})
router.get('/api/paper/search', async function (req, res) {
  let page = parseInt(req.query.page)
  let size = parseInt(req.query.size)
  let startDate = req.query.date ? req.query.date[0] + ' 00:00:00' : '1900-00-00 00:00:00'
  let endDate = req.query.date ? req.query.date[1] + ' 00:00:00' : '2100-00-00 00:00:00'
  let pubs = req.query.pubs ? req.query.pubs : []
  let params = [{ date: { $gte: startDate, $lte: endDate } }, { publication: { $in: pubs } }]
  req.query.area ? params.push({ areas: req.query.area }) : params
  if (req.query.text) {
    let reg = new RegExp(req.query.text, 'i')
    let selector = { $or: [{ title: { $regex: reg } }, { abstract: { $regex: reg } }, { DOI: { $regex: reg } }, { authors: { $regex: reg } }] }
    params.push(selector)
  }
  data = await Paper.aggregate([
    {
      $match: { $and: params }
    },
    { $sort: { date: -1, _id: 1 } },
    {
      $facet: {
        total: [{ $count: 'total' }],
        groupPub: [
          {
            $group: {
              _id: '$publication',
              value: { $sum: 1 }
            }
          }
        ],
        groupArea: [
          { $unwind: '$areas' },
          {
            $group: {
              _id: '$areas',
              value: { $sum: 1 }
            }
          }
        ],
        data: [{ $skip: (page - 1) * size }, { $limit: size }]
      }
    }
  ])
  res.send(data)
})
router.post('/api/paper', async function (req, res) {
  let data = req.body
  console.log('收到', data.DOI)
  try {
    if (await Paper.findOne({ DOI: data.DOI })) {
      res.status(500).send('数据已存在')
      console.log('已存在')
    } else {
      await new Paper(data).save()
      console.log('存储成功')
      res.status(200).send('存储成功')
    }
  } catch (err) {
    res.status(500).send('数据库存储出错:' + err)
    console.log('catch: ', err)
  }
})

module.exports = router
