const express = require('express')
const bodyParser = require('body-parser')
const cors = require('cors')

//引入路由容器
let router = require('./router')

let server = express()

server.use(bodyParser.json())
server.use(bodyParser.urlencoded({ extended: true }))
server.use(cors())

server.use('/public/', express.static('./public/'))
server.use('/node_modules/', express.static('./node_modules/'))

//挂载路由容器到服务中
server.use(router)

server.listen(4000)
